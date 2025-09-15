import { Component } from '@angular/core';
import { EmployeeService } from '../../services/employee/employee.service';
import { TestListingService } from '../../services/test-listing/test-listing.service';
import { ToastService } from '../../services/toast/toast.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-feedback-result',
  imports: [FormsModule,CommonModule],
  templateUrl: './feedback-result.component.html',
  styleUrl: './feedback-result.component.css'
})
export class FeedbackResultComponent {
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

    // Attempted employees for selected test
    attemptedEmployees: any[] = [];

    // Assignment controls
    dueDate: string = '';
    assignmentResult: any = null;
    error: string = '';
  
    constructor(
      private employeeService: EmployeeService,
      private testListingService: TestListingService,
      private toastService: ToastService,
      private router: Router
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
      this.attemptedEmployees = [];
      if (testId) {
        this.testListingService.getTestAttempts(testId).subscribe({
          next: (data: any) => {
            this.attemptedEmployees = data.attempts || [];
          },
          error: (error) => {
            console.error('Error fetching test attempts:', error);
            this.attemptedEmployees = [];
          }
        });
      }
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
  
    // Load tests created by the current user
    loadTests(): void {
      this.testListingService.getTestsCreatedBySelf().subscribe({
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
  
    // Generate stable pending assessments count based on employee ID
    getPendingAssessmentsCount(employeeId: number): number {
      // Generate a consistent "random" number based on employee ID
      // This ensures the same employee always shows the same count
      return (employeeId % 5) + 1;
    }
  
    // Format tech stack display
    formatTechStack(techStack: any): string {
      // Handle null, undefined, or empty values
      if (!techStack || techStack === null || techStack === undefined) {
        return 'Not specified';
      }
      
      // If it's already a string, return it
      if (typeof techStack === 'string') {
        return techStack.trim() || 'Not specified';
      }
      
      // If it's an array, join the elements
      if (Array.isArray(techStack)) {
        const filteredArray = techStack.filter(item => item && item.toString().trim() !== '');
        return filteredArray.length > 0 ? filteredArray.join(', ') : 'Not specified';
      }
      
      // If it's an object (JSON structure from backend)
      if (typeof techStack === 'object') {
        // Handle empty objects
        if (Object.keys(techStack).length === 0) {
          return 'Not specified';
        }
        
        // The tech_stack is a JSON object with skill names as keys and levels as values
        // e.g., {"python": "intermediate", "javascript": "advanced"}
        const techStackEntries = Object.entries(techStack)
          .filter(([key, value]) => {
            // Filter out null, undefined, empty strings, and non-string values
            return value && (typeof value === 'string' || typeof value === 'number') && key.trim() !== '';
          })
          .map(([key, value]) => `${key.charAt(0).toUpperCase() + key.slice(1)} (${value})`)
          .join(', ');
        
        return techStackEntries || 'Not specified';
      }
      
      return 'Not specified';
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

    // Redirect to results page based on attempt type
    viewAttemptResult(attempt: any): void {
      console.log("attempt",attempt)
      if (attempt.quiz) {
        this.router.navigate(['/results/', attempt.test_id]);
      } else {
        this.router.navigate(['/debug-results/', attempt.test_id]);
      }
    }
}
