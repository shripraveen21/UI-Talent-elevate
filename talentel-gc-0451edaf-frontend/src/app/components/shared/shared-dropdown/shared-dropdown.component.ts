import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
export interface DropdownOption {
  id: string | number;
  name: string;
}

@Component({
  selector: 'app-shared-dropdown',
  imports:[CommonModule],
  templateUrl: './shared-dropdown.component.html',
  styleUrls: ['./shared-dropdown.component.css']
})
export class SharedDropdownComponent {
  @Input() options: DropdownOption[] = [];
  @Input() selectedOption: DropdownOption | null = null;
  @Input() placeholder: string = 'Select Option';
  @Input() label: string = '';
  @Input() disabled: boolean = false;

  @Output() selectionChange = new EventEmitter<DropdownOption>();

  showDropdown = false;

  selectOption(option: DropdownOption) {
    this.selectionChange.emit(option);
    this.showDropdown = false;
  }

  toggleDropdown() {
    if (!this.disabled) {
      this.showDropdown = !this.showDropdown;
    }
  }

  onBlur(event: FocusEvent) {
    // Close dropdown if focus leaves
    setTimeout(() => {
      this.showDropdown = false;
    }, 150);
  }
}
