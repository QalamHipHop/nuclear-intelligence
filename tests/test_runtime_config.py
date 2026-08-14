"""Tests for secret-safe environment handling."""
from __future__ import annotations

import unittest

from core.runtime_config import mask_secret, runtime_secret_status, validate_secret


class RuntimeSecretsTests(unittest.TestCase):
    def test_hf_token_is_validated_without_exposing_value(self) -> None:
        env = {"HF_TOKEN": "hf_example_valid_shape"}
        status = validate_secret("HF_TOKEN", prefix="hf_", environ=env)
        self.assertTrue(status.usable)
        public = status.public_dict()
        self.assertNotIn("hf_example", repr(public))

    def test_invalid_and_placeholder_values_are_not_usable(self) -> None:
        self.assertFalse(validate_secret("HF_TOKEN", prefix="hf_", environ={"HF_TOKEN": "hf_..."}).usable)
        self.assertFalse(validate_secret("HF_TOKEN", prefix="hf_", environ={"HF_TOKEN": "github_value"}).usable)
        self.assertFalse(validate_secret("GITHUB_TOKEN", environ={}).usable)

    def test_runtime_status_contains_only_public_fields(self) -> None:
        status = runtime_secret_status(environ={"HF_TOKEN": "hf_secret_value"})
        self.assertTrue(status["HF_TOKEN"]["usable"])
        self.assertNotIn("secret_value", repr(status))
        self.assertEqual(mask_secret(""), "<unset>")
        self.assertNotEqual(mask_secret("hf_secret_value"), "hf_secret_value")


if __name__ == "__main__":
    unittest.main()
