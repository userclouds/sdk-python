import pytest
from authz_sample import run_authz_sample
from tokenizer_sample import run_tokenizer_sample
from usercloudssdk.client import Client
from userstore_sample import run_userstore_sample


class TestSDKSamples:
    @pytest.fixture(params=[{}, {"timeout": 5}])
    def ucclient(self, request) -> Client:
        return Client.from_env(**request.param)

    def test_authz(self, ucclient: Client) -> None:
        run_authz_sample(ucclient)

    def test_tokenizer(self, ucclient: Client) -> None:
        run_tokenizer_sample(ucclient)

    def test_userstore(self, ucclient: Client) -> None:
        run_userstore_sample(ucclient)
