def test_list_metrics(quotient_client):
    metrics = quotient_client.list_metrics()
    assert metrics is not None, "Expected metrics to be returned"
    assert isinstance(metrics, list), "Expected metrics to be a list"
    assert len(metrics) > 0, "Expected at least one metric to be returned"
    for metric in metrics:
        assert isinstance(metric, dict), "Expected each metric to be an object"
        assert "title" in metric, "Expected each metric to have a 'title' field"
