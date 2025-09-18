import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { Toast, ToastType, ToastConfig } from '../../models/interface/toast';

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  private toastsSubject = new BehaviorSubject<Toast[]>([]);
  private maxToasts = 5;
  private defaultDuration = 5000; // 5 seconds

  public toasts$: Observable<Toast[]> = this.toastsSubject.asObservable();

  constructor() {}

  /**
   * Show a success toast notification
   * @param message - The message to display
   * @param config - Optional configuration
   */
  showSuccess(message: string, config?: ToastConfig): string {
    return this.addToast({
      type: ToastType.SUCCESS,
      message,
      ...config
    });
  }

  /**
   * Show an error toast notification
   * @param message - The message to display
   * @param config - Optional configuration
   */
  showError(message: string, config?: ToastConfig): string {
    return this.addToast({
      type: ToastType.ERROR,
      message,
      duration: config?.duration || 7000, // Longer duration for errors
      ...config
    });
  }

  /**
   * Show an info toast notification
   * @param message - The message to display
   * @param config - Optional configuration
   */
  showInfo(message: string, config?: ToastConfig): string {
    return this.addToast({
      type: ToastType.INFO,
      message,
      ...config
    });
  }

  /**
   * Show a warning toast notification
   * @param message - The message to display
   * @param config - Optional configuration
   */
  showWarning(message: string, config?: ToastConfig): string {
    return this.addToast({
      type: ToastType.WARNING,
      message,
      duration: config?.duration || 6000, // Slightly longer for warnings
      ...config
    });
  }

  /**
   * Dismiss a specific toast by ID
   * @param toastId - The ID of the toast to dismiss
   */
  dismiss(toastId: string): void {
    const currentToasts = this.toastsSubject.value;
    const updatedToasts = currentToasts.filter(toast => toast.id !== toastId);
    this.toastsSubject.next(updatedToasts);
  }

  /**
   * Dismiss all toasts
   */
  dismissAll(): void {
    this.toastsSubject.next([]);
  }

  /**
   * Get the current toasts
   */
  getCurrentToasts(): Toast[] {
    return this.toastsSubject.value;
  }

  /**
   * Set the maximum number of toasts to display
   * @param max - Maximum number of toasts
   */
  setMaxToasts(max: number): void {
    this.maxToasts = max;
    this.enforceMaxToasts();
  }

  /**
   * Set the default duration for toasts
   * @param duration - Duration in milliseconds
   */
  setDefaultDuration(duration: number): void {
    this.defaultDuration = duration;
  }

  private addToast(config: {
    type: ToastType;
    message: string;
    duration?: number;
    dismissible?: boolean;
  }): string {
    const toast: Toast = {
      id: this.generateId(),
      type: config.type,
      message: config.message,
      duration: config.duration ?? this.defaultDuration,
      dismissible: config.dismissible ?? true,
      timestamp: new Date()
    };

    const currentToasts = this.toastsSubject.value;
    const updatedToasts = [toast, ...currentToasts];
    
    // Enforce max toasts limit
    if (updatedToasts.length > this.maxToasts) {
      updatedToasts.splice(this.maxToasts);
    }

    this.toastsSubject.next(updatedToasts);
    return toast.id;
  }

  private enforceMaxToasts(): void {
    const currentToasts = this.toastsSubject.value;
    if (currentToasts.length > this.maxToasts) {
      const trimmedToasts = currentToasts.slice(0, this.maxToasts);
      this.toastsSubject.next(trimmedToasts);
    }
  }

  private generateId(): string {
    return `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  // Convenience methods for common scenarios
  
  /**
   * Show login success toast
   */
  showLoginSuccess(): string {
    return this.showSuccess('Login successful! Welcome back.');
  }

  /**
   * Show login error toast
   */
  showLoginError(error?: string): string {
    return this.showError(error || 'Login failed. Please check your credentials.');
  }

  /**
   * Show quiz saved toast
   */
  showQuizSaved(): string {
    return this.showSuccess('Quiz saved successfully!');
  }

  /**
   * Show debug exercise created toast
   */
  showDebugExerciseCreated(): string {
    return this.showSuccess('Debug exercise created successfully!');
  }

  /**
   * Show mail sent toast
   */
  showMailSent(): string {
    return this.showSuccess('Mail sent successfully!');
  }

  /**
   * Show mail not sent toast
   */
  showMailNotSent(error?: string): string {
    return this.showError(error || 'Failed to send mail. Please try again.');
  }

  /**
   * Show assessment assigned toast
   */
  showAssessmentAssigned(): string {
    return this.showSuccess('Assessment assigned successfully!');
  }

  /**
   * Show data saved toast
   */
  showDataSaved(): string {
    return this.showSuccess('Data saved successfully!');
  }

  /**
   * Show network error toast
   */
  showNetworkError(): string {
    return this.showError('Network error. Please check your connection and try again.');
  }

  /**
   * Show validation error toast
   */
  showValidationError(message: string): string {
    return this.showWarning(message);
  }

  /**
   * Generic showToast method for compatibility
   * @param config - Toast configuration object
   */
  showToast(config: {
    message: string;
    type: 'success' | 'error' | 'info' | 'warning';
    duration?: number;
  }): string {
    switch (config.type) {
      case 'success':
        return this.showSuccess(config.message, { duration: config.duration });
      case 'error':
        return this.showError(config.message, { duration: config.duration });
      case 'info':
        return this.showInfo(config.message, { duration: config.duration });
      case 'warning':
        return this.showWarning(config.message, { duration: config.duration });
      default:
        return this.showInfo(config.message, { duration: config.duration });
    }
  }

  /**
   * Alias for dismiss method for compatibility
   * @param toastId - The ID of the toast to dismiss
   */
  dismissToast(toastId: string): void {
    this.dismiss(toastId);
  }
}