import json
import re

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from quotientai.exceptions import logger


@dataclass
class Trace:
    """
    Represents a trace from the QuotientAI API
    """
    
    trace_id: str
    root_span: Optional[Dict[str, Any]] = None
    total_duration_ms: float = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    span_list: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.span_list is None:
            self.span_list = []
    
    def __rich_repr__(self):  # pragma: no cover
        yield "id", self.trace_id
        yield "total_duration_ms", self.total_duration_ms

        if self.start_time:
            yield "start_time", self.start_time
        if self.end_time:
            yield "end_time", self.end_time


class Traces:
    """
    Container for traces that matches the API response schema.
    """
    
    def __init__(self, data: List[Trace], count: int):
        self.data = data
        self.count = count

    def __repr__(self):
        return f"Traces(count={self.count}, data=[{type(self.data[0] if self.data else None)}])"
    
    def to_jsonl(self, filename: Optional[str] = None) -> str:
        """
        Export traces to JSON Lines format.
        
        Args:
            filename: Optional filename to save the JSON Lines data to
            
        Returns:
            String containing JSON Lines data
        """
        jsonl_lines = []
        for trace in self.data:
            # Convert Trace object to dict for JSON serialization
            trace_dict = {
                "trace_id": trace.trace_id,
                "root_span": trace.root_span,
                "total_duration_ms": trace.total_duration_ms,
                "start_time": trace.start_time.isoformat() if trace.start_time else None,
                "end_time": trace.end_time.isoformat() if trace.end_time else None,
                "span_list": trace.span_list,
            }
            jsonl_lines.append(json.dumps(trace_dict))
        
        jsonl_data = "\n".join(jsonl_lines)
        
        if filename:
            with open(filename, 'w') as f:
                f.write(jsonl_data)
        
        return jsonl_data


class TracesResource:
    """
    Resource for interacting with traces in the Quotient API.
    """

    def __init__(self, client):
        self._client = client

    def list(
        self,
        *,
        time_range: Optional[str] = None,
        app_name: Optional[str] = None,
        environments: Optional[List[str]] = None,
        compress: bool = True,
    ) -> Traces:
        """
        List traces with optional filtering parameters.

        Args:
            time_range: Optional time range filter (e.g., "1d", "30m", "6M"). Valid units: "d" for days, "m" for minutes, "M" for months. Hours are not supported.
            app_name: Optional app name filter
            environments: Optional list of environments to filter by
            compress: Whether to request compressed response

        Returns:
            Traces object containing traces and total count
        """
        try:
            params = {}
            if time_range:
                params["time_range"] = time_range
                # First add spaces between numbers and units using regex
                params["time_range"] = re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', params["time_range"])
                # Then convert time range with proper pluralization
                # Extract number and unit, then convert with pluralization
                match = re.match(r'(\d+)\s+([a-zA-Z]+)', params["time_range"])
                if match:
                    number = int(match.group(1))
                    unit = match.group(2)
                    
                    # Convert units with pluralization
                    if unit == "d":
                        params["time_range"] = f"{number} {'DAY' if number == 1 else 'DAYS'}"
                    elif unit == "m":
                        params["time_range"] = f"{number} {'MINUTE' if number == 1 else 'MINUTES'}"
                    elif unit == "M":
                        params["time_range"] = f"{number} {'MONTH' if number == 1 else 'MONTHS'}"
                    # Note: 'h' (hours) is not a valid unit, so we don't handle it
                
            if app_name:
                params["app_name"] = app_name
            if environments:
                params["environments"] = environments
            if compress:
                params["compress"] = "true"

            headers = {}
            if compress:
                headers["Accept-Encoding"] = "gzip"

            # the response is already decompressed by httpx
            # https://www.python-httpx.org/quickstart/#binary-response-content
            response = self._client._get("/traces", params=params)

            # Convert trace dictionaries to Trace objects
            trace_objects = []
            for trace_dict in response.get("traces", []):
                # Parse datetime fields
                start_time = None
                if trace_dict.get("start_time"):
                    start_time = datetime.fromisoformat(trace_dict["start_time"].replace('Z', '+00:00'))
                
                end_time = None
                if trace_dict.get("end_time"):
                    end_time = datetime.fromisoformat(trace_dict["end_time"].replace('Z', '+00:00'))
                
                trace = Trace(
                    trace_id=trace_dict["trace_id"],
                    root_span=trace_dict.get("root_span"),
                    total_duration_ms=trace_dict.get("total_duration_ms", 0),
                    start_time=start_time,
                    end_time=end_time,
                    span_list=trace_dict.get("span_list", []),
                )
                trace_objects.append(trace)

            traces = Traces(
                data=trace_objects,
                count=len(trace_objects),
            )
                
        except Exception as e:
            logger.error(f"Error listing traces: {str(e)}")
            raise

        # Return Traces object with structured response
        return traces

    def get(self, trace_id: str) -> Trace:
        """
        Get a specific trace by its ID.

        Args:
            trace_id: The ID of the trace to retrieve

        Returns:
            Trace object containing the trace data
        """
        try:
            response = self._client._get(f"/traces/{trace_id}")
            
            # Response is already parsed JSON from @handle_errors decorator
            trace_dict = response
            
            # Parse datetime fields
            start_time = None
            if trace_dict.get("start_time"):
                start_time = datetime.fromisoformat(trace_dict["start_time"].replace('Z', '+00:00'))
            
            end_time = None
            if trace_dict.get("end_time"):
                end_time = datetime.fromisoformat(trace_dict["end_time"].replace('Z', '+00:00'))
            
            trace = Trace(
                trace_id=trace_dict["trace_id"],
                root_span=trace_dict.get("root_span"),
                total_duration_ms=trace_dict.get("total_duration_ms", 0),
                start_time=start_time,
                end_time=end_time,
                span_list=trace_dict.get("span_list", []),
            )
        except Exception as e:
            logger.error(f"Error getting trace {trace_id}: {str(e)}")
            raise

        return trace

