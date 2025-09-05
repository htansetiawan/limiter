"""
Configuration management for Rate Limiter
"""

from typing import Dict, Any
import os


class Config:
    """Configuration manager for rate limiter settings"""

    DEFAULTS = {
        'algorithm': 'token_bucket',
        'rate': 10.0,
        'duration': 60,
        'request_rate': 15.0,
        'burst_size': 5,
        'live_display': False
    }

    ALGORITHMS = ['token_bucket', 'leaky_bucket', 'sliding_window', 'fixed_window']

    def __init__(self):
        self.settings = self.DEFAULTS.copy()

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.settings[key] = value

    def update_from_dict(self, config_dict: Dict[str, Any]):
        """Update configuration from dictionary"""
        for key, value in config_dict.items():
            if key in self.settings:
                self.settings[key] = value

    def validate_algorithm(self, algorithm: str) -> bool:
        """Validate algorithm name"""
        return algorithm in self.ALGORITHMS

    def get_available_algorithms(self) -> list:
        """Get list of available algorithms"""
        return self.ALGORITHMS.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        return self.settings.copy()


# Global configuration instance
config = Config()
