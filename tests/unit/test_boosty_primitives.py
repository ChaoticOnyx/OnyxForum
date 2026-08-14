import datetime
import hashlib
import hmac
import importlib.util
import json
import unittest
from decimal import Decimal
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
BOOSTY = REPOSITORY / "modules" / "hub" / "hub" / "features" / "donations" / "boosty"


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, str(BOOSTY / filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


opyx = load_module("boosty_opyx_primitives", "opyx.py")
signing = load_module("boosty_signing_primitives", "signing.py")
api = load_module("boosty_api_primitives", "api.py")
webhook_payload = load_module("boosty_webhook_payload_primitives", "webhook_payload.py")
formatting = load_module("boosty_formatting_primitives", "formatting.py")


def settings(**overrides):
    values = {
        "boosty_opyx_rate": "2",
        "boosty_rounding": "floor",
        "boosty_minimum_donation": "0",
        "boosty_maximum_opyx_enabled": False,
        "boosty_maximum_opyx": "0",
        "boosty_bonus_enabled": False,
        "boosty_bonus_rules": "[]",
    }
    values.update(overrides)
    return values


class BoostyOpyxCalculationTest(unittest.TestCase):
    def test_decimal_bonus_rounding_and_snapshot(self):
        result = opyx.calculate_opyx(
            Decimal("1000.25"),
            settings(
                boosty_opyx_rate="2",
                boosty_bonus_enabled=True,
                boosty_bonus_rules='[{"minimum":"1000","percent":"5"}]',
            ),
        )
        self.assertTrue(result.eligible)
        self.assertEqual(result.base_rate, Decimal("2"))
        self.assertEqual(result.bonus_percent, Decimal("5"))
        self.assertEqual(result.final_rate, Decimal("2.10"))
        self.assertEqual(result.opyx, Decimal("2100"))

        changed_settings = settings(boosty_opyx_rate="20")
        self.assertEqual(result.final_rate, Decimal("2.10"))
        self.assertEqual(opyx.calculate_opyx("1000.25", changed_settings).opyx, Decimal("20005"))

    def test_minimum_cap_and_rounding_modes(self):
        below = opyx.calculate_opyx("9.99", settings(boosty_minimum_donation="10"))
        self.assertFalse(below.eligible)
        self.assertEqual(below.opyx, Decimal("0"))

        capped = opyx.calculate_opyx(
            "100",
            settings(
                boosty_maximum_opyx_enabled=True,
                boosty_maximum_opyx="75",
            ),
        )
        self.assertEqual(capped.opyx, Decimal("75"))
        self.assertEqual(opyx.calculate_opyx("1.01", settings(boosty_opyx_rate="1", boosty_rounding="ceil")).opyx, Decimal("2"))
        self.assertEqual(opyx.calculate_opyx("1.49", settings(boosty_opyx_rate="1", boosty_rounding="half_up")).opyx, Decimal("1"))

    def test_non_positive_values_never_credit_points(self):
        self.assertFalse(opyx.calculate_opyx("0", settings()).eligible)
        self.assertFalse(opyx.calculate_opyx("10", settings(boosty_opyx_rate="0")).eligible)


class BoostyTransportPrimitivesTest(unittest.TestCase):
    def test_link_token_expiry_is_formatted_in_moscow_time(self):
        expires_at = datetime.datetime.fromisoformat("2026-08-15T00:00:59.383754+00:00")
        self.assertEqual(
            formatting.format_moscow_datetime(expires_at),
            "15.08.2026, 03:00 по МСК",
        )

    def test_api_json_amount_is_parsed_as_decimal(self):
        response = type("Response", (), {"text": '{"amount":0.1,"count":1}'})()
        payload = api.BoostyApiClient._payload(response)
        self.assertIsInstance(payload["amount"], Decimal)
        self.assertEqual(payload["amount"], Decimal("0.1"))

    def test_short_boosty_page_uses_server_offset(self):
        self.assertEqual(
            api.next_page_offset(0, 11, {"total": 24, "offset": "11"}, 50),
            "11",
        )
        self.assertEqual(
            api.next_page_offset("11", 11, {"total": 24, "offset": "22"}, 50),
            "22",
        )
        self.assertIsNone(
            api.next_page_offset("22", 2, {"total": 24, "offset": "24"}, 50)
        )

    def test_boosty_page_fallback_without_metadata(self):
        self.assertEqual(api.next_page_offset(0, 50, {}, 50), 50)
        self.assertIsNone(api.next_page_offset(50, 3, {}, 50))

    def test_event_external_id_is_stable_and_actor_specific(self):
        first = {
            "eventType": "subscribe",
            "createdAt": 1786745146,
            "amount": Decimal("100"),
            "user": {"id": 13002707},
        }
        reordered = {
            "user": {"id": 13002707},
            "amount": Decimal("100"),
            "createdAt": 1786745146,
            "eventType": "subscribe",
        }
        another_actor = dict(first, user={"id": 43839647})
        self.assertEqual(api.event_external_id(first), api.event_external_id(reordered))
        self.assertNotEqual(api.event_external_id(first), api.event_external_id(another_actor))
        self.assertTrue(api.event_external_id(first).startswith("event:"))

    def test_webhook_envelope_and_hmac_sha256(self):
        created_at = datetime.datetime(2026, 8, 14, 12, 0, tzinfo=datetime.timezone.utc)
        body = signing.serialize_envelope("event-1", "boosty.donation.processed", created_at, {"opyx": "200"})
        expected = hmac.new(b"secret", ("1723636800." + body).encode("utf-8"), hashlib.sha256).hexdigest()
        self.assertEqual(signing.calculate_signature("secret", "1723636800", body), "sha256=" + expected)
        self.assertIn('"event":"boosty.donation.processed"', body)
        self.assertIn('"eventId":"event-1"', body)

    def test_discord_webhook_payload_contains_a_message(self):
        envelope = {
            "eventId": "event-1",
            "event": "boosty.donation.processed",
            "createdAt": "2026-08-14T12:00:00+00:00",
            "data": {"opyx": "200"},
        }
        body = webhook_payload.serialize_delivery_payload(
            envelope,
            "https://discord.com/api/webhooks/123/token",
        )
        payload = json.loads(body)
        self.assertTrue(payload["content"])
        self.assertEqual(payload["embeds"][0]["title"], "boosty.donation.processed")
        self.assertIn('"opyx": "200"', payload["embeds"][0]["description"])
        self.assertEqual(payload["allowed_mentions"], {"parse": []})

    def test_non_discord_webhook_keeps_canonical_envelope(self):
        envelope = {
            "eventId": "event-1",
            "event": "boosty.test",
            "createdAt": "2026-08-14T12:00:00+00:00",
            "data": {"message": "test"},
        }
        body = webhook_payload.serialize_delivery_payload(
            envelope,
            "https://example.org/hooks/boosty",
        )
        self.assertEqual(json.loads(body), envelope)
        self.assertFalse(webhook_payload.is_discord_webhook_url(
            "https://discord.com.evil.test/api/webhooks/1/token"
        ))


class BoostySafetyBoundaryTest(unittest.TestCase):
    def test_boosty_feature_does_not_reference_money_transactions(self):
        sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in BOOSTY.rglob("*")
            if path.suffix in {".py", ".html"}
        )
        self.assertNotIn("MoneyTransaction", sources)
        self.assertNotIn("money_transaction", sources)

    def test_boosty_points_use_the_standard_hub_action(self):
        source = (BOOSTY / "service.py").read_text(encoding="utf-8")
        self.assertIn("add_points_transaction_and_notify", source)
        self.assertIn("dispatch_points_transaction_notifications", source)
        self.assertNotIn("PointsTransaction(", source)

    def test_database_model_has_duplicate_protection(self):
        source = (BOOSTY / "models.py").read_text(encoding="utf-8")
        self.assertIn('external_id = Column(db_hub.String(128), nullable=False, unique=True)', source)
        self.assertIn('points_transaction_id = Column(db_hub.Integer', source)
        self.assertIn('nullable=True, unique=True)', source)

    def test_required_technical_settings_are_in_cfg(self):
        source = (REPOSITORY / "modules" / "hub" / "hub" / "configs" / "example" / "boosty.cfg").read_text(encoding="utf-8")
        for key in (
            "BOOSTY_API_BASE_URL",
            "BOOSTY_POLLING_INTERVAL_SECONDS",
            "BOOSTY_API_TIMEOUT_SECONDS",
            "BOOSTY_API_RETRY_COUNT",
            "BOOSTY_OPERATION_MAX_ATTEMPTS",
            "BOOSTY_EVENTS_INITIAL_BACKFILL_DAYS",
            "BOOSTY_EVENTS_LOOKBACK_SECONDS",
            "BOOSTY_WEBHOOK_DEFAULT_TIMEOUT_SECONDS",
            "BOOSTY_PUBLIC_LINK_URL",
            "BOOSTY_LINK_TOKEN_RESEND_COOLDOWN_SECONDS",
        ):
            self.assertIn(key, source)

    def test_gift_purchase_is_not_a_points_event(self):
        source = (BOOSTY / "constants.py").read_text(encoding="utf-8")
        self.assertIn('POINTS_EVENT_TYPES = frozenset(("donation_author", "subscribe", "recurrent"))', source)
        self.assertNotIn('POINTS_EVENT_TYPES = frozenset(("buy_gift"', source)

    def test_expired_link_token_requires_an_explicit_reissue(self):
        service = (BOOSTY / "service.py").read_text(encoding="utf-8")
        form = (BOOSTY / "forms.py").read_text(encoding="utf-8")
        template = (
            REPOSITORY / "modules" / "hub" / "hub" / "templates" /
            "features" / "donations" / "boosty_link.html"
        ).read_text(encoding="utf-8")
        self.assertIn("def ensure_link_token(account, settings=None, allow_reissue=False):", service)
        self.assertIn("def request_new_link_token(email, settings=None):", service)
        self.assertIn("allow_reissue=True", service)
        self.assertIn("class BoostyLinkTokenRequestForm", form)
        self.assertIn('name="action" value="request_token"', template)


if __name__ == "__main__":
    unittest.main()
