import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

// Interface for button configuration to ensure type safety
export interface ButtonConfig {
  text: string;                    // Required: Button display text
  svgIcon?: string;               // Optional: SVG path data for icon
  width?: string;                 // Required: Button width (e.g., 'w-full', 'w-48', '200px')
  height?: string;                // Required: Button height (e.g., 'h-12', 'py-3', '48px')
  disabled?: boolean;             // Optional: Disabled state
  loading?: boolean;              // Optional: Loading state with different text
  loadingText?: string;           // Optional: Text to show when loading
  variant?: 'primary' | 'secondary' | 'danger'; // Optional: Button style variant
}

@Component({
  selector: 'app-reusable-button',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './reusable-button.component.html',
  styleUrls: ['./reusable-button.component.css']
})
export class ReusableButtonComponent {
  // Required inputs
  @Input() text!: string;                    // Button text - required
  @Input() width!: string;                   // Button width - required
  @Input() height!: string;                  // Button height - required
  
  // Optional inputs with defaults
  @Input() svgIcon?: string;                 // Optional SVG icon path
  @Input() disabled: boolean = false;        // Disabled state
  @Input() loading: boolean = false;         // Loading state
  @Input() loadingText: string = 'Loading...'; // Loading text
  @Input() variant: 'primary' | 'secondary' | 'danger' = 'primary'; // Style variant
  
  // Event emitter for click handling
  @Output() buttonClick = new EventEmitter<void>();
  
  /**
   * Handle button click events
   * Emits the buttonClick event if button is not disabled or loading
   */
  onButtonClick(): void {
    if (!this.disabled && !this.loading) {
      this.buttonClick.emit();
    }
  }
  
  /**
   * Generate CSS classes for the button based on current state and variant
   * Combines base styling with variant-specific classes
   */
  getButtonClasses(): string {
    const baseClasses = `
      font-medium text-sm border border-transparent rounded-md
      hover:shadow-glow hover:-translate-y-1 hover:scale-105
      transition-all duration-200 transform
      focus:outline-none focus:ring-2 focus:ring-offset-2
      disabled:cursor-not-allowed disabled:opacity-60
      disabled:hover:transform-none disabled:hover:shadow-none
      flex items-center justify-center space-x-2
    `.replace(/\s+/g, ' ').trim();
    
    let variantClasses = '';
    let focusClasses = '';
    
    // Apply disabled state styling - override variant colors when disabled
    if (this.isButtonDisabled()) {
      variantClasses = 'bg-blue-400 text-white';
      focusClasses = 'focus:ring-blue-500';
    } else {
      // Apply variant-specific styling when not disabled
      switch (this.variant) {
        case 'primary':
          variantClasses = 'bg-gradient-hero text-white';
          focusClasses = 'focus:ring-blue-500';
          break;
        case 'secondary':
          variantClasses = 'bg-gray-100 text-gray-700 hover:bg-gray-200';
          focusClasses = 'focus:ring-gray-500';
          break;
        case 'danger':
          variantClasses = 'bg-red-600 text-white hover:bg-red-700';
          focusClasses = 'focus:ring-red-500';
          break;
      }
    }
    
    return `${baseClasses} ${variantClasses} ${focusClasses} ${this.width} ${this.height}`;
  }
  
  /**
   * Get the display text based on loading state
   * Returns loading text if loading, otherwise returns normal text
   */
  getDisplayText(): string {
    return this.loading ? this.loadingText : this.text;
  }
  
  /**
   * Check if button should be disabled
   * Button is disabled if explicitly disabled or in loading state
   */
  isButtonDisabled(): boolean {
    return this.disabled || this.loading;
  }
}