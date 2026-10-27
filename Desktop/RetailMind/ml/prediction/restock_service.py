'''Restock Intelligence module

Provides the RestockIntelligence class used by the ML service to calculate
reorder recommendations and status classifications for each product.

The implementation follows the revised business rules described in the
user request:

* Safety stock is 15 % of the predicted demand.
* Required stock = predicted demand + safety stock.
* Reorder quantity = max(0, required_stock – current_stock).
* Coverage ratio = current_stock / predicted_demand (0 if predicted demand is 0).
* Status determination uses coverage thresholds and the product's minimum
  stock level:
  - OUT OF STOCK: current_stock == 0
  - RESTOCK: current_stock <= minimum_stock
  - MONITOR: stock covers demand but is below the monitor buffer
  - NO IMMEDIATE ACTION: sufficient stock beyond monitor buffer

The class is deliberately lightweight and has no external dependencies so
it can be imported safely during unit tests.
''' 

# Constants – can be tuned via configuration if needed
SAFETY_STOCK_RATIO = 0.15
OVERSTOCK_THRESHOLD = 2.0  # retained for compatibility
RESTOCK_SOON_COVERAGE = 0.9  # retained constant, not used in three‑status logic
MONITOR_UPPER_COVERAGE = 1.1  # retained constant, not used in three‑status logic

class RestockIntelligence:
    """Calculate restock metrics and status for a product.

    The ``calculate`` method mirrors the signature used throughout the code
    base: ``calculate(current_stock, predicted_demand, minimum_stock=None)``.
    ``minimum_stock`` may be ``None`` – the caller passes the value extracted
    from the product document.
    """

    def __init__(self, safety_stock_ratio: float = 0.15, monitor_threshold: float = 0.25, overstock_threshold: float = 2.0):
        """Create a RestockIntelligence instance.

        Parameters
        ----------
        safety_stock_ratio: float, default 0.15
            Fraction of predicted demand to keep as safety stock.
        monitor_threshold: float, default 0.25
            Upper buffer (as a fraction of the replenishment threshold) that
            defines the ``MONITOR`` window.
        overstock_threshold: float, default 2.0
            Retained for compatibility; not used in three‑status logic.
        """
        self.safety_stock_ratio = safety_stock_ratio
        self.monitor_threshold = monitor_threshold
        self.overstock_threshold = overstock_threshold

    def calculate(self, current_stock: float, predicted_demand: float, minimum_stock: float = None):
        """Return a dictionary with reorder information and status.

        Parameters
        ----------
        current_stock: float
            Current on‑hand inventory for the product.
        predicted_demand: float
            Demand forecast produced by the ML model (units for the forecast
            horizon – daily in this project).
        minimum_stock: float, optional
            The user‑defined reorder point. If ``None`` it is treated as 0.
        """
        # Safety stock and required stock
        safety_stock = predicted_demand * self.safety_stock_ratio
        required_stock = predicted_demand + safety_stock
        reorder_quantity = max(0.0, required_stock - current_stock)

        # Coverage ratio – guard against division by zero
        coverage_ratio = (current_stock / predicted_demand) if predicted_demand > 0 else 0.0

        # Minimum stock fallback to 0 when not provided
        min_stock = minimum_stock if minimum_stock is not None else 0.0

        # Determine status using the three‑canonical logic
        if current_stock == 0 or current_stock <= min_stock or current_stock < predicted_demand:
            status = "RESTOCK"
        else:
            replenishment_threshold = max(min_stock, required_stock)
            monitor_upper = replenishment_threshold * (1 + self.monitor_threshold)
            if current_stock < required_stock or current_stock <= monitor_upper:
                status = "MONITOR"
            else:
                status = "NO IMMEDIATE ACTION"

        return {
            "reorder_quantity": int(round(reorder_quantity)),
            "safety_stock": int(round(safety_stock)),
            "required_stock": int(round(required_stock)),
            "coverage_ratio": round(coverage_ratio, 2),
            "status": status,
        }
