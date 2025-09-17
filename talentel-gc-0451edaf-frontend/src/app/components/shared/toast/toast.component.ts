import { Component, Input, Output, EventEmitter, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Toast, ToastType } from '../../../models/interface/toast';

@Component({
  selector: 'app-toast',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './toast.component.html',
  styleUrls: ['./toast.component.css']
})
export class ToastComponent implements OnInit, OnDestroy {
  @Input() toast!: Toast;
  @Output() dismiss = new EventEmitter<string>();

  private timeoutId?: number;
  public isVisible = false;

  ngOnInit() {
    // Trigger animation after component initialization
    setTimeout(() => {
      this.isVisible = true;
    }, 10);

    // Auto-dismiss if duration is set
    if (this.toast.duration && this.toast.duration > 0) {
      this.timeoutId = window.setTimeout(() => {
        this.onDismiss();
      }, this.toast.duration);
    }
  }

  ngOnDestroy() {
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }
  }

  onDismiss() {
    this.isVisible = false;
    // Wait for animation to complete before emitting dismiss
    setTimeout(() => {
      this.dismiss.emit(this.toast.id);
    }, 300);
  }

  getToastClasses(): string {
    const baseClasses = 'fixed top-5 right-5 toast-transition transform';
    const visibilityClasses = this.isVisible 
      ? 'translate-y-0 opacity-100' 
      : 'translate-y-2 opacity-0';

    return `${baseClasses} ${visibilityClasses}`;
  }

  getDefaultTitle(): string {
    switch (this.toast.type) {
      case ToastType.SUCCESS:
        return 'Success!';
      case ToastType.ERROR:
        return 'Error!';
      case ToastType.INFO:
        return 'Information';
      case ToastType.WARNING:
        return 'Warning!';
      default:
        return 'Notification';
    }
  }

  getIconClasses(): string {
    switch (this.toast.type) {
      case ToastType.SUCCESS:
        return 'text-success';
      case ToastType.ERROR:
        return 'text-error';
      case ToastType.INFO:
        return 'text-primary';
      case ToastType.WARNING:
        return 'text-warning';
      default:
        return 'text-muted-foreground';
    }
  }

  getIcon(): string {
    switch (this.toast.type) {
      case ToastType.SUCCESS:
        return 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z';
      case ToastType.ERROR:
        return 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z';
      case ToastType.INFO:
        return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
      case ToastType.WARNING:
        return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.268 16.5c-.77.833.192 2.5 1.732 2.5z';
      default:
        return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';
    }
  }

  // Get container classes based on toast type
  getToastContainerClasses(): string {
    const baseClasses = 'max-w-xs rounded-xl shadow-lg';
    
    switch (this.toast.type) {
      case ToastType.SUCCESS:
        return `${baseClasses} bg-green-500`;
      case ToastType.ERROR:
        return `${baseClasses} bg-red-500`;
      case ToastType.INFO:
        return `${baseClasses} bg-white border border-gray-200`;
      case ToastType.WARNING:
        return `${baseClasses} bg-white border border-gray-200`;
      default:
        return `${baseClasses} bg-white border border-gray-200`;
    }
  }

  // Get close button classes based on toast type
  getCloseButtonClasses(): string {
    const baseClasses = 'absolute top-2 right-2 inline-flex items-center justify-center w-6 h-6 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2';
    
    switch (this.toast.type) {
      case ToastType.SUCCESS:
        return `${baseClasses} text-white hover:text-green-100 focus:ring-green-300`;
      case ToastType.ERROR:
        return `${baseClasses} text-white hover:text-red-100 focus:ring-red-300`;
      case ToastType.INFO:
        return `${baseClasses} text-gray-400 hover:text-gray-600 focus:ring-blue-500`;
      case ToastType.WARNING:
        return `${baseClasses} text-gray-400 hover:text-gray-600 focus:ring-blue-500`;
      default:
        return `${baseClasses} text-gray-400 hover:text-gray-600 focus:ring-blue-500`;
    }
  }

  // Get title classes based on toast type
  getTitleClasses(): string {
    const baseClasses = 'font-bold pr-6';
    
    switch (this.toast.type) {
      case ToastType.SUCCESS:
        return `${baseClasses} text-white`;
      case ToastType.ERROR:
        return `${baseClasses} text-white`;
      case ToastType.INFO:
        return `${baseClasses} text-gray-800`;
      case ToastType.WARNING:
        return `${baseClasses} text-gray-800`;
      default:
        return `${baseClasses} text-gray-800`;
    }
  }

  // Get message classes based on toast type
  getMessageClasses(): string {
    const baseClasses = 'mt-1 text-sm pr-6';
    
    switch (this.toast.type) {
      case ToastType.SUCCESS:
        return `${baseClasses} text-white`;
      case ToastType.ERROR:
        return `${baseClasses} text-white`;
      case ToastType.INFO:
        return `${baseClasses} text-gray-600`;
      case ToastType.WARNING:
        return `${baseClasses} text-gray-600`;
      default:
        return `${baseClasses} text-gray-600`;
    }
  }
}