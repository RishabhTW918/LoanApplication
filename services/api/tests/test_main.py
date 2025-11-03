import unittest
from fastapi.testclient import TestClient
from services.api.app.main import app, settings
from fastapi import status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from services.common.database import Base, get_db
from services.common.models import LoanApplication
from decimal import Decimal
from uuid import uuid4


client = TestClient(app)


class TestHealthEndpoint(unittest.TestCase):
    def test_root_health_ok_exact_service(self):
        resp = client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.json(),
            {
                "service": settings.app_name,
                "status": "healthy",
                "version": "1.0.0",
            },
        )


class TestApplicationEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # In-memory SQLite and dependency override
        cls.SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
        cls.engine = create_engine(
            cls.SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=cls.engine
        )
        Base.metadata.create_all(bind=cls.engine)

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        # remember original override (if any), then set ours
        cls._orig_override = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = override_get_db

        # client is already defined at module level; reuse it

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=cls.engine)
        # restore previous override (or remove ours)
        if cls._orig_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = cls._orig_override

    def test_openapi_contract_for_application(self):
        """Verify decorator contract: tags + responses + schemas."""
        resp = client.get("/openapi.json")
        self.assertEqual(resp.status_code, 200)
        spec = resp.json()

        post_op = spec["paths"]["/application"]["post"]

        # Tags
        self.assertIn("Applications", post_op.get("tags", []))

        # Responses present
        responses = post_op["responses"]
        for code in ("202", "422", "500"):
            self.assertIn(code, responses)

        # Schemas wired correctly
        ok202_schema = responses["202"]["content"]["application/json"]["schema"]
        self.assertTrue(
            ok202_schema.get("$ref", "").endswith(
                "#/components/schemas/ApplicationResponse"
            )
        )

        for code in ("422", "500"):
            err_schema = responses[code]["content"]["application/json"]["schema"]
            self.assertTrue(
                err_schema.get("$ref", "").endswith(
                    "#/components/schemas/ErrorResponse"
                )
            )

    def test_submit_valid_application_returns_202(self):
        """Happy path: should return 202 and ApplicationResponse shape."""
        payload = {
            "pan_number": "ABCDE1234F",
            "applicant_name": "Rajesh Kumar",
            "monthly_income_inr": 50000,
            "loan_amount_inr": 200000,
            "loan_type": "PERSONAL",
        }
        resp = client.post("/application", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        body = resp.json()
        self.assertIn("application_id", body)
        self.assertEqual(body.get("status"), "PENDING")

    def test_submit_application_missing_field_returns_422(self):
        """Missing required field -> FastAPI validation error 422."""
        payload = {
            "pan_number": "ABCDE1234F",
            "monthly_income_inr": 50000,
            # "loan_amount_inr" missing
            "loan_type": "PERSONAL",
        }
        resp = client.post("/application", json=payload)
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("detail", resp.json())

    def test_submit_application_invalid_pan_returns_422(self):
        payload = {
            "pan_number": "INVALID",  # too short / wrong pattern
            "monthly_income_inr": 50000,
            "loan_amount_inr": 200000,
            "loan_type": "PERSONAL",
        }
        resp = client.post("/application", json=payload)
        self.assertEqual(resp.status_code, 422)  # avoid deprecated constant
        data = resp.json()
        self.assertIn("detail", data)
        # at least verify the error points at pan_number
        self.assertTrue(
            any(it.get("loc", [])[-1] == "pan_number" for it in data["detail"])
        )

    def test_openapi_contract_for_application_status(self):
        """Verify /applications/{id}/status contract (tags, responses, schemas)."""
        resp = client.get("/openapi.json")
        self.assertEqual(resp.status_code, 200)
        spec = resp.json()

        get_op = spec["paths"]["/applications/{application_id}/status"]["get"]

        # Tags
        self.assertIn("Applications", get_op.get("tags", []))

        # Responses present
        responses = get_op["responses"]
        for code in ("200", "404"):
            self.assertIn(code, responses)

        # Schemas wired correctly
        ok200_schema = responses["200"]["content"]["application/json"]["schema"]
        self.assertTrue(
            ok200_schema.get("$ref", "").endswith(
                "#/components/schemas/ApplicationStatusResponse"
            )
        )
        err404_schema = responses["404"]["content"]["application/json"]["schema"]
        self.assertTrue(
            err404_schema.get("$ref", "").endswith("#/components/schemas/ErrorResponse")
        )

    def test_get_existing_application_status_returns_200(self):
        """Create an application in DB and fetch its status."""
        app_id = uuid4()
        db = (
            self.TestingSessionSessionLocal()
            if hasattr(self, "TestingSessionSessionLocal")
            else self.TestingSessionLocal()
        )
        try:
            db_app = LoanApplication(
                id=app_id,
                pan_number="ABCDE1234F",
                applicant_name="Rajesh Kumar",
                monthly_income_inr=Decimal("50000"),
                loan_amount_inr=Decimal("200000"),
                loan_type="PERSONAL",
                status="PENDING",
            )
            db.add(db_app)
            db.commit()

            resp = client.get(f"/applications/{app_id}/status")
            self.assertEqual(resp.status_code, 200)
            body = resp.json()
            self.assertEqual(body["application_id"], str(app_id))
            self.assertEqual(body["status"], "PENDING")
            self.assertIn("created_at", body)
            self.assertIn("updated_at", body)
            self.assertIn("cibil_score", body)  # may be null
        finally:
            db.close()

    def test_get_nonexistent_application_status_returns_404(self):
        fake_id = uuid4()
        resp = client.get(f"/applications/{fake_id}/status")
        self.assertEqual(resp.status_code, 404)
        detail = resp.json().get("detail", "")
        # allow either full message or just the UUID presence
        self.assertIn(str(fake_id).lower(), detail.lower())
