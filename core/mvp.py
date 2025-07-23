"""
MVP (Model-View-Presenter) Pattern Implementation

This module provides base classes for implementing the MVP pattern,
promoting separation of concerns and testability.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal


class BaseModel(QObject):
    """
    Base model class for MVP pattern.
    
    Models handle data and business logic, independent of UI.
    """
    
    # Signals for notifying views of data changes
    data_changed = pyqtSignal(str, object)  # property_name, new_value
    data_added = pyqtSignal(object)         # new_item
    data_removed = pyqtSignal(object)       # removed_item
    data_updated = pyqtSignal(object)       # updated_item
    error_occurred = pyqtSignal(str)        # error_message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self._validators = {}
        self._observers = []
    
    def set_data(self, key: str, value: Any) -> bool:
        """
        Set data with validation.
        
        Args:
            key: Data key
            value: Data value
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate if validator exists
            if key in self._validators:
                if not self._validators[key](value):
                    self.error_occurred.emit(f"Validation failed for {key}")
                    return False
            
            old_value = self._data.get(key)
            self._data[key] = value
            
            # Emit change signal if value actually changed
            if old_value != value:
                self.data_changed.emit(key, value)
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Error setting {key}: {str(e)}")
            return False
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data value."""
        return self._data.get(key, default)
    
    def has_data(self, key: str) -> bool:
        """Check if key exists in data."""
        return key in self._data
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all data as dictionary."""
        return self._data.copy()
    
    def clear_data(self) -> None:
        """Clear all data."""
        self._data.clear()
        self.data_changed.emit("*", None)
    
    def add_validator(self, key: str, validator: Callable[[Any], bool]) -> None:
        """Add validator for a data key."""
        self._validators[key] = validator
    
    def add_observer(self, observer: 'BasePresenter') -> None:
        """Add observer to be notified of data changes."""
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: 'BasePresenter') -> None:
        """Remove observer."""
        if observer in self._observers:
            self._observers.remove(observer)


class BaseView(ABC):
    """
    Abstract base view class for MVP pattern.
    
    Views handle UI display and user interactions,
    delegating logic to presenters.
    """
    
    def __init__(self):
        self._presenter: Optional['BasePresenter'] = None
    
    def set_presenter(self, presenter: 'BasePresenter') -> None:
        """Set the presenter for this view."""
        self._presenter = presenter
    
    def get_presenter(self) -> Optional['BasePresenter']:
        """Get the presenter for this view."""
        return self._presenter
    
    @abstractmethod
    def display_data(self, data: Any) -> None:
        """Display data in the view."""
        pass
    
    @abstractmethod
    def display_error(self, error_message: str) -> None:
        """Display error message in the view."""
        pass
    
    @abstractmethod
    def display_status(self, status_message: str) -> None:
        """Display status message in the view."""
        pass
    
    @abstractmethod
    def get_user_input(self) -> Dict[str, Any]:
        """Get user input from the view."""
        pass
    
    @abstractmethod
    def clear_display(self) -> None:
        """Clear the view display."""
        pass
    
    def enable_controls(self, enabled: bool = True) -> None:
        """Enable/disable controls in the view."""
        pass
    
    def show_loading(self, loading: bool = True) -> None:
        """Show/hide loading indicator."""
        pass


class BasePresenter(QObject):
    """
    Base presenter class for MVP pattern.
    
    Presenters mediate between views and models,
    handling user interactions and business logic.
    """
    
    # Signals for communication
    view_update_requested = pyqtSignal(object)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, model: BaseModel = None, view: BaseView = None):
        super().__init__()
        self._model = model
        self._view = view
        self._is_initialized = False
        
        # Connect signals if model and view are provided
        if self._model:
            self._connect_model_signals()
        if self._view:
            self._view.set_presenter(self)
    
    def set_model(self, model: BaseModel) -> None:
        """Set the model for this presenter."""
        if self._model:
            self._disconnect_model_signals()
        
        self._model = model
        self._connect_model_signals()
    
    def set_view(self, view: BaseView) -> None:
        """Set the view for this presenter."""
        self._view = view
        if self._view:
            self._view.set_presenter(self)
    
    def get_model(self) -> Optional[BaseModel]:
        """Get the model."""
        return self._model
    
    def get_view(self) -> Optional[BaseView]:
        """Get the view."""
        return self._view
    
    def initialize(self) -> bool:
        """
        Initialize the presenter.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self._model or not self._view:
                return False
            
            # Perform initialization logic
            self._setup_initial_data()
            self._is_initialized = True
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"Initialization failed: {str(e)}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self._model:
            self._disconnect_model_signals()
        self._is_initialized = False
    
    def _connect_model_signals(self) -> None:
        """Connect model signals to presenter handlers."""
        if self._model:
            self._model.data_changed.connect(self._on_model_data_changed)
            self._model.data_added.connect(self._on_model_data_added)
            self._model.data_removed.connect(self._on_model_data_removed)
            self._model.data_updated.connect(self._on_model_data_updated)
            self._model.error_occurred.connect(self._on_model_error)
    
    def _disconnect_model_signals(self) -> None:
        """Disconnect model signals."""
        if self._model:
            self._model.data_changed.disconnect(self._on_model_data_changed)
            self._model.data_added.disconnect(self._on_model_data_added)
            self._model.data_removed.disconnect(self._on_model_data_removed)
            self._model.data_updated.disconnect(self._on_model_data_updated)
            self._model.error_occurred.disconnect(self._on_model_error)
    
    def _setup_initial_data(self) -> None:
        """Setup initial data. Override in subclasses."""
        pass
    
    # Model event handlers
    def _on_model_data_changed(self, property_name: str, new_value: Any) -> None:
        """Handle model data change."""
        if self._view:
            if property_name == "*":
                # Full data refresh
                self._view.display_data(self._model.get_all_data())
            else:
                # Specific property change
                self._update_view_property(property_name, new_value)
    
    def _on_model_data_added(self, new_item: Any) -> None:
        """Handle new data addition."""
        if self._view:
            self._view.display_data(self._model.get_all_data())
    
    def _on_model_data_removed(self, removed_item: Any) -> None:
        """Handle data removal."""
        if self._view:
            self._view.display_data(self._model.get_all_data())
    
    def _on_model_data_updated(self, updated_item: Any) -> None:
        """Handle data update."""
        if self._view:
            self._view.display_data(self._model.get_all_data())
    
    def _on_model_error(self, error_message: str) -> None:
        """Handle model error."""
        if self._view:
            self._view.display_error(error_message)
        self.error_occurred.emit(error_message)
    
    def _update_view_property(self, property_name: str, new_value: Any) -> None:
        """Update specific property in view. Override in subclasses."""
        pass
    
    # User action handlers - to be overridden in subclasses
    def handle_user_action(self, action: str, data: Dict[str, Any] = None) -> bool:
        """
        Handle user actions from the view.
        
        Args:
            action: Action name
            data: Action data
            
        Returns:
            bool: True if handled successfully, False otherwise
        """
        return False
    
    def refresh_data(self) -> bool:
        """Refresh data. Override in subclasses."""
        return False
    
    def save_data(self) -> bool:
        """Save data. Override in subclasses."""
        return False
    
    def load_data(self) -> bool:
        """Load data. Override in subclasses.""" 
        return False
    
    def validate_data(self) -> bool:
        """Validate current data. Override in subclasses."""
        return True
    
    # Status and error handling
    def set_status(self, message: str) -> None:
        """Set status message."""
        self.status_changed.emit(message)
        if self._view:
            self._view.display_status(message)
    
    def set_error(self, error_message: str) -> None:
        """Set error message."""
        self.error_occurred.emit(error_message)
        if self._view:
            self._view.display_error(error_message)


class MVPFactory:
    """
    Factory for creating MVP components.
    
    Helps with dependency injection and component creation.
    """
    
    @staticmethod
    def create_mvp_triad(model_class, view_class, presenter_class, 
                        model_args=None, view_args=None, presenter_args=None):
        """
        Create complete MVP triad with proper connections.
        
        Args:
            model_class: Model class
            view_class: View class  
            presenter_class: Presenter class
            model_args: Model constructor arguments
            view_args: View constructor arguments
            presenter_args: Presenter constructor arguments
            
        Returns:
            tuple: (model, view, presenter)
        """
        # Create instances
        model_args = model_args or []
        view_args = view_args or []
        presenter_args = presenter_args or []
        
        model = model_class(*model_args)
        view = view_class(*view_args)
        presenter = presenter_class(model, view, *presenter_args)
        
        # Initialize
        if not presenter.initialize():
            raise RuntimeError("Failed to initialize MVP triad")
        
        return model, view, presenter