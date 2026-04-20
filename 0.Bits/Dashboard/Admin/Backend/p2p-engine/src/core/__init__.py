"""
Core module - shared types, base classes, state management, and utilities.
"""

from .state_manager import state_manager, StateManager, ManagedOrder, OrderState, OrderEvent
from .registry import registry, ClientRegistry
