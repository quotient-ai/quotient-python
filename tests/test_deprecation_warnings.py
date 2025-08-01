"""
Tests for deprecation warnings when using old parameters in QuotientAI SDK
"""

import pytest
import warnings
from unittest.mock import Mock, patch, AsyncMock

from quotientai.client import QuotientAI
from quotientai.async_client import AsyncQuotientAI
from quotientai.types import DetectionType


@pytest.fixture
def mock_logs_resource():
    """Mock logs resource for testing"""
    mock_resource = Mock()
    mock_resource.create = Mock(return_value="test-log-id")
    return mock_resource


@pytest.fixture
def quotient_client_with_mock_resource(mock_logs_resource):
    """QuotientAI client with mocked logs resource"""
    with patch("quotientai.client._BaseQuotientClient") as MockClient:
        mock_instance = MockClient.return_value
        client = QuotientAI(api_key="test-api-key")
        client.logs = mock_logs_resource
        yield client


@pytest.fixture
def async_quotient_client_with_mock_resource(mock_logs_resource):
    """AsyncQuotientAI client with mocked logs resource"""
    with patch("quotientai.async_client._AsyncQuotientClient") as MockClient, patch(
        "quotientai.resources.auth.AsyncAuthResource"
    ) as MockAuthResource:
        mock_instance = MockClient.return_value
        mock_auth = MockAuthResource.return_value
        mock_auth.authenticate = AsyncMock()
        mock_instance._get = AsyncMock()
        mock_instance._post = AsyncMock()
        mock_instance._patch = AsyncMock()
        mock_instance._delete = AsyncMock()

        # Make logs.create an AsyncMock
        mock_logs_resource.create = AsyncMock(return_value="test-log-id-async")

        client = AsyncQuotientAI(api_key="test-api-key")
        client.logs = mock_logs_resource
        yield client


class TestSyncDeprecationWarnings:
    """Test deprecation warnings for synchronous QuotientAI client"""

    def test_deprecated_params_in_logger_init_triggers_warning(
        self, quotient_client_with_mock_resource
    ):
        """Test that using deprecated parameters in logger.init() triggers DeprecationWarning"""
        client = quotient_client_with_mock_resource

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            logger = client.logger.init(
                app_name="test-app",
                environment="test",
                hallucination_detection=True,
                hallucination_detection_sample_rate=0.8,
            )

            # Verify warning was triggered
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated as of 0.3.4" in str(w[0].message)
            assert "hallucination_detection" in str(w[0].message)
            assert "detection_sample_rate" in str(w[0].message)

            # Verify logger was still created and configured correctly
            assert logger is not None
            assert logger._configured is True
            assert DetectionType.HALLUCINATION in logger.detections
            assert logger.detection_sample_rate == 0.8

    def test_deprecated_params_in_logger_init_with_inconsistency_detection(
        self, quotient_client_with_mock_resource
    ):
        """Test that inconsistency_detection parameter is handled (but not supported in v2)"""
        client = quotient_client_with_mock_resource

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            logger = client.logger.init(
                app_name="test-app",
                environment="test",
                hallucination_detection=True,
                inconsistency_detection=True,  # This should be ignored in v2
                hallucination_detection_sample_rate=0.5,
            )

            # Verify warning was triggered
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)

            # Verify inconsistency detection is not included (not supported in v2)
            assert DetectionType.HALLUCINATION in logger.detections
            assert len(logger.detections) == 1  # Only hallucination, not inconsistency

    def test_mixing_deprecated_and_new_params_in_logger_init_fails(
        self, quotient_client_with_mock_resource, caplog
    ):
        """Test that mixing deprecated and new parameters in logger.init() fails"""
        client = quotient_client_with_mock_resource

        logger = client.logger.init(
            app_name="test-app",
            environment="test",
            # Mix old and new parameters
            hallucination_detection=True,
            detections=[DetectionType.DOCUMENT_RELEVANCY],
            detection_sample_rate=1.0,
        )

        # Should return None (failure) and log error
        assert logger is None
        assert "Cannot mix deprecated parameters" in caplog.text

    def test_deprecated_params_in_log_method_triggers_warning(
        self, quotient_client_with_mock_resource
    ):
        """Test that using deprecated parameters in log() method triggers warning"""
        client = quotient_client_with_mock_resource

        # Initialize logger without detection parameters
        client.logger.init(
            app_name="test-app",
            environment="test",
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            log_id = client.log(
                user_query="Test query",
                model_output="Test output",
                documents=["Test document"],
                hallucination_detection=True,
                hallucination_detection_sample_rate=0.7,
            )

            # Verify warning was triggered
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated as of 0.3.4" in str(w[0].message)
            assert (
                "Document relevancy is not available with deprecated parameters"
                in str(w[0].message)
            )

            # Verify log was still created
            assert log_id == "test-log-id"

    def test_mixing_deprecated_and_new_params_in_log_method_fails(
        self, quotient_client_with_mock_resource, caplog
    ):
        """Test that mixing deprecated and new parameters in log() method fails"""
        client = quotient_client_with_mock_resource

        # Initialize logger with new parameters
        client.logger.init(
            app_name="test-app",
            environment="test",
            detections=[DetectionType.HALLUCINATION],
            detection_sample_rate=1.0,
        )

        log_id = client.log(
            user_query="Test query",
            model_output="Test output",
            documents=["Test document"],
            # Mix new and old parameters
            detections=[DetectionType.DOCUMENT_RELEVANCY],
            hallucination_detection=True,
        )

        # Should return None (failure) and log error
        assert log_id is None
        assert "Cannot mix deprecated parameters" in caplog.text

    def test_deprecated_params_require_user_query_and_model_output(
        self, quotient_client_with_mock_resource, caplog
    ):
        """Test that deprecated parameters require user_query and model_output"""
        client = quotient_client_with_mock_resource

        client.logger.init(
            app_name="test-app",
            environment="test",
        )

        # Test without user_query
        log_id = client.log(
            # user_query missing
            model_output="Test output",
            documents=["Test document"],
            hallucination_detection=True,
        )

        assert log_id is None
        assert (
            "user_query and model_output are required when using deprecated parameters"
            in caplog.text
        )

        # Clear logs
        caplog.clear()

        # Test without model_output
        log_id = client.log(
            user_query="Test query",
            # model_output missing
            documents=["Test document"],
            hallucination_detection=True,
        )

        assert log_id is None
        assert (
            "user_query and model_output are required when using deprecated parameters"
            in caplog.text
        )

    def test_new_params_work_without_warnings(self, quotient_client_with_mock_resource):
        """Test that new parameters work without triggering warnings"""
        client = quotient_client_with_mock_resource

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Use new parameters
            logger = client.logger.init(
                app_name="test-app",
                environment="test",
                detections=[
                    DetectionType.HALLUCINATION,
                    DetectionType.DOCUMENT_RELEVANCY,
                ],
                detection_sample_rate=1.0,
            )

            log_id = client.log(
                user_query="Test query",
                model_output="Test output",
                documents=["Test document"],
            )

            # No warnings should be triggered
            deprecation_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) == 0

            # Verify everything works correctly
            assert logger is not None
            assert log_id == "test-log-id"


class TestAsyncDeprecationWarnings:
    """Test deprecation warnings for asynchronous AsyncQuotientAI client"""

    def test_deprecated_params_in_async_logger_init_triggers_warning(
        self, async_quotient_client_with_mock_resource
    ):
        """Test that using deprecated parameters in async logger.init() triggers warning"""
        client = async_quotient_client_with_mock_resource

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            logger = client.logger.init(
                app_name="test-app",
                environment="test",
                hallucination_detection=True,
                hallucination_detection_sample_rate=0.6,
            )

            # Verify warning was triggered
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated as of 0.3.4" in str(w[0].message)

            # Verify logger was configured correctly
            assert logger is not None
            assert DetectionType.HALLUCINATION in logger.detections

    @pytest.mark.asyncio
    async def test_deprecated_params_in_async_log_method_triggers_warning(
        self, async_quotient_client_with_mock_resource
    ):
        """Test that using deprecated parameters in async log() method triggers warning"""
        client = async_quotient_client_with_mock_resource

        client.logger.init(
            app_name="test-app",
            environment="test",
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            log_id = await client.log(
                user_query="Test query",
                model_output="Test output",
                documents=["Test document"],
                hallucination_detection=True,
                hallucination_detection_sample_rate=0.9,
            )

            # Verify warning was triggered
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated as of 0.3.4" in str(w[0].message)

            # Verify log was created
            assert log_id == "test-log-id-async"

    def test_mixing_deprecated_and_new_params_in_async_logger_init_fails(
        self, async_quotient_client_with_mock_resource, caplog
    ):
        """Test that mixing deprecated and new parameters in async logger.init() fails"""
        client = async_quotient_client_with_mock_resource

        logger = client.logger.init(
            app_name="test-app",
            environment="test",
            # Mix parameters
            hallucination_detection=True,
            detections=[DetectionType.HALLUCINATION],
        )

        assert logger is None
        assert "Cannot mix deprecated parameters" in caplog.text

    @pytest.mark.asyncio
    async def test_mixing_deprecated_and_new_params_in_async_log_method_fails(
        self, async_quotient_client_with_mock_resource, caplog
    ):
        """Test that mixing deprecated and new parameters in async log() method fails"""
        client = async_quotient_client_with_mock_resource

        client.logger.init(
            app_name="test-app",
            environment="test",
            detections=[DetectionType.DOCUMENT_RELEVANCY],
        )

        log_id = await client.log(
            user_query="Test query",
            documents=["Test document"],
            # Mix parameters
            hallucination_detection=True,
            detections=[DetectionType.HALLUCINATION],
        )

        assert log_id is None
        assert "Cannot mix deprecated parameters" in caplog.text

    @pytest.mark.asyncio
    async def test_new_params_work_without_warnings_async(
        self, async_quotient_client_with_mock_resource
    ):
        """Test that new parameters work without warnings in async client"""
        client = async_quotient_client_with_mock_resource

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            logger = client.logger.init(
                app_name="test-app",
                environment="test",
                detections=[
                    DetectionType.HALLUCINATION,
                    DetectionType.DOCUMENT_RELEVANCY,
                ],
                detection_sample_rate=0.5,
            )

            log_id = await client.log(
                user_query="Test query",
                model_output="Test output",
                documents=["Test document"],
                detections=[DetectionType.HALLUCINATION],
                detection_sample_rate=1.0,
            )

            # No deprecation warnings should be triggered
            deprecation_warnings = [
                warning
                for warning in w
                if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) == 0

            # Verify everything works
            assert logger is not None
            assert log_id == "test-log-id-async"


class TestDeprecationWarningMessages:
    """Test specific deprecation warning message content"""

    def test_warning_message_content_in_init(self, quotient_client_with_mock_resource):
        """Test that deprecation warning messages contain expected content"""
        client = quotient_client_with_mock_resource

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            client.logger.init(
                app_name="test-app",
                environment="test",
                hallucination_detection=True,
                inconsistency_detection=True,
                hallucination_detection_sample_rate=0.5,
            )

            warning_message = str(w[0].message)

            # Check for specific deprecated parameter names
            assert "hallucination_detection" in warning_message
            assert "inconsistency_detection" in warning_message
            assert "hallucination_detection_sample_rate" in warning_message

            # Check for new parameter suggestions
            assert "detections" in warning_message
            assert "detection_sample_rate" in warning_message

            # Check for version information
            assert "0.3.4" in warning_message

    def test_warning_message_content_in_log(self, quotient_client_with_mock_resource):
        """Test that deprecation warning messages in log method contain expected content"""
        client = quotient_client_with_mock_resource

        client.logger.init(
            app_name="test-app",
            environment="test",
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            client.log(
                user_query="Test query",
                model_output="Test output",
                documents=["Test document"],
                hallucination_detection=True,
                inconsistency_detection=True,
                hallucination_detection_sample_rate=0.3,
            )

            warning_message = str(w[0].message)

            # Check for document relevancy limitation message
            assert (
                "Document relevancy is not available with deprecated parameters"
                in warning_message
            )

            # Check for version and parameter information
            assert "0.3.4" in warning_message
            assert "deprecated" in warning_message
