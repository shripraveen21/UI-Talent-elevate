import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReusableButtonComponent } from './reusable-button.component';

@Component({
  selector: 'app-reusable-button-demo',
  standalone: true,
  imports: [CommonModule, ReusableButtonComponent],
  template: `
    <div class="container mx-auto max-w-4xl px-4 py-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-8 text-center">Reusable Button Component Demo</h1>
      
      <!-- Basic Usage Examples -->
      <div class="bg-white p-6 rounded-lg border border-gray-200 shadow-sm mb-8">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">Basic Usage Examples</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          
          <!-- Primary Button with Icon (Original Style) -->
          <div class="space-y-2">
            <h3 class="text-sm font-medium text-gray-600">Primary with Lightning Icon</h3>
            <app-reusable-button
              text="Generate Learning Concepts"
              [svgIcon]="lightningIcon"
              width="w-full"
              height="py-3 px-6"
              variant="primary"
              (buttonClick)="onButtonClick('Primary with Icon')">
            </app-reusable-button>
          </div>
          
          <!-- Secondary Button -->
          <div class="space-y-2">
            <h3 class="text-sm font-medium text-gray-600">Secondary Button</h3>
            <app-reusable-button
              text="Cancel"
              width="w-full"
              height="py-2 px-4"
              variant="secondary"
              (buttonClick)="onButtonClick('Secondary')">
            </app-reusable-button>
          </div>
          
          <!-- Danger Button -->
          <div class="space-y-2">
            <h3 class="text-sm font-medium text-gray-600">Danger Button</h3>
            <app-reusable-button
              text="Delete"
              [svgIcon]="trashIcon"
              width="w-full"
              height="py-2 px-4"
              variant="danger"
              (buttonClick)="onButtonClick('Danger')">
            </app-reusable-button>
          </div>
        </div>
      </div>
      
      <!-- Size Variations -->
      <div class="bg-white p-6 rounded-lg border border-gray-200 shadow-sm mb-8">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">Size Variations</h2>
        <div class="space-y-4">
          
          <!-- Small Button -->
          <div class="flex items-center space-x-4">
            <span class="w-20 text-sm text-gray-600">Small:</span>
            <app-reusable-button
              text="Small Button"
              width="w-32"
              height="py-1 px-3 text-xs"
              variant="primary"
              (buttonClick)="onButtonClick('Small')">
            </app-reusable-button>
          </div>
          
          <!-- Medium Button -->
          <div class="flex items-center space-x-4">
            <span class="w-20 text-sm text-gray-600">Medium:</span>
            <app-reusable-button
              text="Medium Button"
              width="w-40"
              height="py-2 px-4"
              variant="primary"
              (buttonClick)="onButtonClick('Medium')">
            </app-reusable-button>
          </div>
          
          <!-- Large Button -->
          <div class="flex items-center space-x-4">
            <span class="w-20 text-sm text-gray-600">Large:</span>
            <app-reusable-button
              text="Large Button"
              width="w-48"
              height="py-3 px-6"
              variant="primary"
              (buttonClick)="onButtonClick('Large')">
            </app-reusable-button>
          </div>
          
          <!-- Full Width Button -->
          <div class="space-y-2">
            <span class="text-sm text-gray-600">Full Width:</span>
            <app-reusable-button
              text="Full Width Button"
              width="w-full"
              height="py-3 px-6"
              variant="primary"
              (buttonClick)="onButtonClick('Full Width')">
            </app-reusable-button>
          </div>
        </div>
      </div>
      
      <!-- State Examples -->
      <div class="bg-white p-6 rounded-lg border border-gray-200 shadow-sm mb-8">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">Button States</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          
          <!-- Normal State -->
          <div class="space-y-2">
            <h3 class="text-sm font-medium text-gray-600">Normal State</h3>
            <app-reusable-button
              text="Click Me"
              width="w-full"
              height="py-2 px-4"
              variant="primary"
              (buttonClick)="onButtonClick('Normal')">
            </app-reusable-button>
          </div>
          
          <!-- Loading State -->
          <div class="space-y-2">
            <h3 class="text-sm font-medium text-gray-600">Loading State</h3>
            <app-reusable-button
              text="Submit"
              width="w-full"
              height="py-2 px-4"
              variant="primary"
              [loading]="true"
              loadingText="Processing..."
              (buttonClick)="onButtonClick('Loading')">
            </app-reusable-button>
          </div>
          
          <!-- Disabled State -->
          <div class="space-y-2">
            <h3 class="text-sm font-medium text-gray-600">Disabled State</h3>
            <app-reusable-button
              text="Disabled"
              width="w-full"
              height="py-2 px-4"
              variant="primary"
              [disabled]="true"
              (buttonClick)="onButtonClick('Disabled')">
            </app-reusable-button>
          </div>
        </div>
      </div>
      
      <!-- Interactive Demo -->
      <div class="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
        <h2 class="text-xl font-semibold text-gray-800 mb-4">Interactive Demo</h2>
        <div class="space-y-4">
          <p class="text-gray-600">Click any button to see the interaction:</p>
          <div class="bg-gray-50 p-4 rounded-md">
            <p class="text-sm text-gray-700">Last clicked: <span class="font-medium">{{ lastClicked || 'None' }}</span></p>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .container {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
  `]
})
export class ReusableButtonDemoComponent {
  lastClicked: string = '';
  
  // SVG icon paths for demonstration
  lightningIcon = 'M13 10V3L4 14h7v7l9-11h-7z';
  trashIcon = 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16';
  
  /**
   * Handle button click events from the demo buttons
   * Updates the lastClicked property to show interaction feedback
   */
  onButtonClick(buttonType: string): void {
    this.lastClicked = `${buttonType} button at ${new Date().toLocaleTimeString()}`;
    console.log(`Button clicked: ${buttonType}`);
  }
}