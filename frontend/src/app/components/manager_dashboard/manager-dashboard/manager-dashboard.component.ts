import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EmployeeService } from '../../../services/employee/employee.service';
import { TestListingService } from '../../../services/test-listing/test-listing.service';
import { ToastService } from '../../../services/toast/toast.service';

@Component({
  selector: 'app-manager-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './manager-dashboard.component.html',
  styleUrls: ['./manager-dashboard.component.css']
})
export class ManagerDashboardComponent implements OnInit {
  showFiltersPanel = false;
  isAssigning = false; // Loading state for assignment
  
  // Expose Math to template
  Math = Math;

  // Employee data
  employees: any[] = [];
  totalEmployees = 0;
  selectedEmployeeIds: number[] = [];

  // Filters
  bands: string[] = [];
  roles: string[] = [];
  skillLevels: string[] = [];
  selectedBand = '';
  selectedRole = '';
  selectedSkillLevel = '';
  search = '';

  // Test data
  tests: any[] = [];
  filteredTests: any[] = [];
  testSearchQuery = '';
  selectedTestId: number | null = null;

  // Assignment controls
  dueDate: string = '';
  assignmentResult: any = null;
  error: string = '';

  constructor(
    private employeeService: EmployeeService,
    private testListingService: TestListingService,
    private toastService: ToastService
  ) {}

  ngOnInit(): void {
    this.loadFilters();
    this.loadEmployees();
    this.loadTests();
  }

  // Toggle filters panel
  toggleFiltersPanel(): void {
    this.showFiltersPanel = !this.showFiltersPanel;
  }

  // Select test method
  selectTest(testId: number): void {
    this.selectedTestId = testId;
    this.onTestSelected();
  }


  // Load filter options
  loadFilters(): void {
    this.employeeService.getEmployeeFilterOptions().subscribe({
      next: (data: any) => {
        this.bands = data.bands || [];
        this.roles = data.roles || [];
        this.skillLevels = data.skill_levels || data.skills || [];
      },
      error: (error) => {
        console.error('Error loading filters:', error);
        this.handleError(error);
      }
    });
  }

  // Load employees with filters
  loadEmployees(): void {
    const params: any = {};
    if (this.selectedBand) params.band = this.selectedBand;
    if (this.selectedRole) params.designation = this.selectedRole;
    if (this.selectedSkillLevel) params.skill_level = this.selectedSkillLevel;
    if (this.search) params.search = this.search;
    
    this.employeeService.getEmployees(params).subscribe({
      next: (data: any) => {
        this.employees = data.employees || [];
        this.totalEmployees = data.total || 0;
        // Remove deselected employees if not in current page
        this.selectedEmployeeIds = this.selectedEmployeeIds.filter(id =>
          this.employees.some(emp => emp.user_id === id)
        );
      },
      error: (error) => {
        console.error('Error loading employees:', error);
        this.handleError(error);
      }
    });
  }

  // Load tests
  loadTests(): void {
    this.testListingService.getTests().subscribe({
      next: (data: any) => {
        this.tests = data.tests || [];
        this.filteredTests = [...this.tests];
      },
      error: (error) => {
        console.error('Error loading tests:', error);
        this.handleError(error);
      }
    });
  }

  // Test search functionality
  onTestSearchChange(): void {
    if (!this.testSearchQuery.trim()) {
      this.filteredTests = [...this.tests];
    } else {
      const query = this.testSearchQuery.toLowerCase();
      this.filteredTests = this.tests.filter(test => 
        test.test_name?.toLowerCase().includes(query) ||
        test.description?.toLowerCase().includes(query) ||
        test.test_type?.toLowerCase().includes(query) ||
        test.difficulty?.toLowerCase().includes(query)
      );
    }
  }

  // Filter change handler
  onEmployeeFilterChange(): void {
    this.loadEmployees();
  }

  // Test selection handler
  onTestSelected(): void {
    this.resetAssignmentState();
  }

  // **FIXED: Actual Backend API Call for Test Assignment**
  assignTest(): void {
    this.resetAssignmentState();
    
    if (!this.validateAssignment()) {
      return;
    }

    this.isAssigning = true;

    const request = {
      user_ids: this.selectedEmployeeIds,
      test_id: this.selectedTestId,
      due_date: this.dueDate // Should be "YYYY-MM-DD"
      // assigned_by: ... // Optionally add if available
    };

    this.testListingService.assignTest(request).subscribe({
      next: (result:any) => {
        this.assignmentResult = result;
        this.isAssigning = false;
        this.toastService.showMailSent();
        // Optional: Clear selections after successful assignment
        // this.selectedEmployeeIds = [];
        // this.selectedTestId = null;
        // this.dueDate = '';
        console.log('Test assigned successfully:', result);
      },
      error: (error:any) => {
        this.isAssigning = false;
        this.handleError(error);
        this.toastService.showMailNotSent('Failed to assign test and send notification email');
        console.error('Error assigning test:', error);
      }
    });
  }

  // Employee checkbox change
  onEmployeeCheckboxChange(userId: number, event: any): void {
    if (event.target.checked) {
      if (!this.selectedEmployeeIds.includes(userId)) {
        this.selectedEmployeeIds.push(userId);
      }
    } else {
      this.selectedEmployeeIds = this.selectedEmployeeIds.filter(id => id !== userId);
    }
  }

  // Select all employees on current page
  isAllSelected(): boolean {
    return this.employees.length > 0 &&
      this.employees.every(emp => this.selectedEmployeeIds.includes(emp.user_id));
  }

  toggleSelectAll(event?: any): void {
    // If called from button click, toggle based on current state
    if (!event || event.type === 'click') {
      if (this.isAllSelected()) {
        // Deselect all employees on current page
        const ids = this.employees.map(emp => emp.user_id);
        this.selectedEmployeeIds = this.selectedEmployeeIds.filter(id => !ids.includes(id));
      } else {
        // Select all employees on current page
        const ids = this.employees.map(emp => emp.user_id);
        this.selectedEmployeeIds = Array.from(new Set([...this.selectedEmployeeIds, ...ids]));
      }
    } else if (event.target.checked) {
      // Select all employees on current page
      const ids = this.employees.map(emp => emp.user_id);
      this.selectedEmployeeIds = Array.from(new Set([...this.selectedEmployeeIds, ...ids]));
    } else {
      // Deselect all employees on current page
      const ids = this.employees.map(emp => emp.user_id);
      this.selectedEmployeeIds = this.selectedEmployeeIds.filter(id => !ids.includes(id));
    }
  }

  // Helper method to get current date for date input min attribute
  getCurrentDate(): string {
    return new Date().toISOString().split('T')[0];
  }

  // Helper method to get selected test name for display
  getSelectedTestName(): string {
    if (!this.selectedTestId) return '';
    const test = this.tests.find(t => t.id === this.selectedTestId);
    return test?.test_name || `Test #${this.selectedTestId}`;
  }

  // Clear all filters
  clearAllFilters(): void {
    this.selectedBand = '';
    this.selectedRole = '';
    this.selectedSkillLevel = '';
    this.search = '';
    this.onEmployeeFilterChange();
  }

  // Check if any filters are active
  hasActiveFilters(): boolean {
    return !!(this.selectedBand || this.selectedRole || this.selectedSkillLevel || this.search);
  }

  // Get count of active filters
  getActiveFiltersCount(): number {
    let count = 0;
    if (this.selectedBand) count++;
    if (this.selectedRole) count++;
    if (this.selectedSkillLevel) count++;
    if (this.search) count++;
    return count;
  }

  // Check if ready to assign test
  isReadyToAssign(): boolean {
    return !!(this.selectedTestId && this.selectedEmployeeIds.length > 0 && this.dueDate);
  }

  // Handle API errors
  private handleError(error: any): void {
    console.error('API Error:', error);
    
    // Extract meaningful error message
    let errorMessage = 'An unexpected error occurred. Please try again.';
    
    if (error?.error?.message) {
      errorMessage = error.error.message;
    } else if (error?.message) {
      errorMessage = error.message;
    } else if (typeof error === 'string') {
      errorMessage = error;
    }
    
    this.error = errorMessage;
  }

  // Reset assignment state
  resetAssignmentState(): void {
    this.assignmentResult = null;
    this.error = '';
  }

  // Validate assignment before submitting
  private validateAssignment(): boolean {
    if (!this.selectedTestId) {
      this.error = 'Please select a test to assign.';
      return false;
    }
    
    if (this.selectedEmployeeIds.length === 0) {
      this.error = 'Please select at least one employee.';
      return false;
    }
    
    if (!this.dueDate) {
      this.error = 'Please set a due date for the assignment.';
      return false;
    }
    
    const selectedDate = new Date(this.dueDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (selectedDate < today) {
      this.error = 'Due date cannot be in the past.';
      return false;
    }
    
    return true;
  }
}
