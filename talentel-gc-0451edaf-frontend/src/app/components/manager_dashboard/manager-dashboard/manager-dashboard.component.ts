import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EmployeeService } from '../../../services/employee/employee.service';
import { TestListingService } from '../../../services/test-listing/test-listing.service';
import { ToastService } from '../../../services/toast/toast.service';
import { SharedDropdownComponent } from '../../shared/shared-dropdown/shared-dropdown.component';
import { BackButtonComponent } from '../../shared/backbutton/backbutton.component';

@Component({
  selector: 'app-manager-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, SharedDropdownComponent, BackButtonComponent],
  templateUrl: './manager-dashboard.component.html',
  styleUrls: ['./manager-dashboard.component.css']
})
export class ManagerDashboardComponent implements OnInit {
  isAssigning = false; // Loading state for assignment
  
  // Expose Math to template
  Math = Math;

  // Employee data
  employees: any[] = [];
  totalEmployees = 0;
  selectedEmployeeIds: number[] = [];

  // Pagination state
  currentPage: number = 1;
  pageSize: number = 10; // Default page size
  totalPages: number = 1;

  // Filters
  bands: string[] = [];
  skillLevels: string[] = [];
  selectedBand = '';
  selectedSkillLevel = '';
  search = '';

  // SharedDropdown for Band Level
  bandLevelOptions: { id: string, name: string }[] = [];
  selectedBandDropdown = { id: '', name: '' };

  onBandLevelChange(option: { id: string | number; name: string }) {
    this.selectedBandDropdown = { id: String(option.id), name: option.name };
    this.selectedBand = String(option.id);
    this.onEmployeeFilterChange();
  }

  // SharedDropdown for Skill Level
  skillLevelOptions = [
    { id: 'BEGINNER', name: 'Beginner' },
    { id: 'INTERMEDIATE', name: 'Intermediate' },
    { id: 'ADVANCED', name: 'Advanced' }
  ];
  selectedSkillLevelDropdown = { id: '', name: '' };

  onSkillLevelChange(option: { id: string | number; name: string }) {
    this.selectedSkillLevelDropdown = { id: String(option.id), name: option.name };
    this.selectedSkillLevel = String(option.id);
    this.onEmployeeFilterChange();
  }

  // Test data
  tests: any[] = [];
  filteredTests: any[] = [];
  testSearchQuery = '';
  selectedTestId: number | null = null;

  // Assessment pagination state
  assessmentPage: number = 1;
  assessmentPageSize: number = 8; // Show 8 assessments per page by default
  assessmentTotalPages: number = 1;

  // Assignment controls
  dueDate: string = '';
  assignmentResult: any = null;
  error: string = '';
  userName: string = '';

  constructor(
    private employeeService: EmployeeService,
    private testListingService: TestListingService,
    private toastService: ToastService
  ) {}

  ngOnInit(): void {
    const userObj = localStorage.getItem('username');
    let userName = 'User';
    if (userObj) {
      try {
        const user = JSON.parse(userObj);
        userName = user.name || 'User';
      } catch {
        userName = userObj || 'User';
      }
    }
    this.userName = userName;
    this.dueDate = this.getCurrentDate(); // Set default due date to today
    this.loadFilters();
    this.loadEmployees();
    this.loadTests();
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
        this.bandLevelOptions = this.bands.map(band => ({ id: band, name: band }));
        this.skillLevels = data.skill_levels || data.skills || [];
        console.log('Loaded skill levels:', this.skillLevels); // Debug log
      },
      error: (error) => {
        console.error('Error loading filters:', error);
        this.handleError(error);
      }
    });
  }

  // Load employees with filters and pagination
  loadEmployees(): void {
    const params: any = {};
    if (this.selectedBand) params.band = this.selectedBand;
    if (this.selectedSkillLevel) params.skill_level = this.selectedSkillLevel;
    if (this.search) params.search = this.search;
    params.page = this.currentPage;
    params.page_size = this.pageSize;

    console.log('[ManagerDashboard] Loading employees with params:', params);

    this.employeeService.getEmployees(params).subscribe({
      next: (data: any) => {
        this.employees = data.employees || [];
        this.totalEmployees = data.total || 0;
        this.totalPages = Math.max(1, Math.ceil(this.totalEmployees / this.pageSize));
        // Remove deselected employees if not in current page
        this.selectedEmployeeIds = this.selectedEmployeeIds.filter(id =>
          this.employees.some(emp => emp.user_id === id)
        );
        console.log(`[ManagerDashboard] Loaded page ${this.currentPage}/${this.totalPages}, employees:`, this.employees.length);
      },
      error: (error) => {
        console.error('[ManagerDashboard] Error loading employees:', error);
        this.handleError(error);
      }
    });
  }

  // Load paginated, filtered tests from backend
  loadTests(): void {
    const params: any = {
      page: this.assessmentPage,
      page_size: this.assessmentPageSize,
      search: this.testSearchQuery || ''
    };
    this.testListingService.getTests(params).subscribe({
      next: (data: any) => {
        this.tests = data.tests || [];
        console.log('[ManagerDashboard] Loaded tests after search:', this.tests);
        this.assessmentTotalPages = Math.max(1, Math.ceil((data.total || this.tests.length) / this.assessmentPageSize));
        // If current page exceeds total pages, reset to last page
        if (this.assessmentPage > this.assessmentTotalPages) {
          this.assessmentPage = this.assessmentTotalPages;
          this.loadTests();
          return;
        }
      },
      error: (error) => {
        console.error('Error loading tests:', error);
        this.handleError(error);
      }
    });
  }

  getPaginatedAssessments(): any[] {
    return this.tests;
  }

  /**
   * Get filtered assessments (for empty state)
   */
  getFilteredAssessments(): any[] {
    return this.tests;
  }

  /**
   * Assessment pagination controls
   */
  goToAssessmentPage(page: number): void {
    if (page < 1 || page > this.assessmentTotalPages) return;
    this.assessmentPage = page;
    this.loadTests();
  }

  nextAssessmentPage(): void {
    if (this.assessmentPage < this.assessmentTotalPages) {
      this.assessmentPage++;
      this.loadTests();
    }
  }

  prevAssessmentPage(): void {
    if (this.assessmentPage > 1) {
      this.assessmentPage--;
      this.loadTests();
    }
  }

  setAssessmentPageSize(size: number): void {
    if (size < 1) return;
    this.assessmentPageSize = size;
    this.assessmentPage = 1;
    this.loadTests();
  }

  // Test search functionality
  onTestSearchChange(): void {
    this.assessmentPage = 1;
    this.loadTests();
  }

  // Filter change handler
  onEmployeeFilterChange(): void {
    this.currentPage = 1; // Reset to first page on filter change
    this.loadEmployees();
  }

  /**
   * Pagination controls
   */
  goToPage(page: number): void {
    if (page < 1 || page > this.totalPages) return;
    this.currentPage = page;
    this.loadEmployees();
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
      this.loadEmployees();
    }
  }

  prevPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadEmployees();
    }
  }

  setPageSize(size: number): void {
    if (size < 1) return;
    this.pageSize = size;
    this.currentPage = 1;
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
        window.history.back()
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

  // Helper method to dynamically determine test type based on test data
  getTestType(test: any): string {
    // Check if test has specific component IDs to determine type
    if (test.quiz_id && test.debug_test_id) {
      return 'MCQ + Debug Exercise';
    } else if (test.quiz_id) {
      return 'MCQ';
    } else if (test.debug_test_id) {
      return 'Debug Exercise';
    } else if (test.test_type) {
      // Use the test_type field if available
      switch (test.test_type.toLowerCase()) {
        case 'mcq':
          return 'MCQ';
        case 'debug-exercise':
          return 'Debug Exercise';
        case 'handson':
          return 'Hands-On';
        case 'debug-mini-project':
          return 'Debug Mini Project';
        default:
          return test.test_type;
      }
    }
    // Default fallback
    return 'MCQ';
  }

  // Clear all filters
  clearAllFilters(): void {
    this.selectedBand = '';
    this.selectedSkillLevel = '';
    this.search = '';
    this.onEmployeeFilterChange();
  }

  // Check if any filters are active
  hasActiveFilters(): boolean {
    return !!(this.selectedBand || this.selectedSkillLevel || this.search);
  }

  // Get count of active filters
  getActiveFiltersCount(): number {
    let count = 0;
    if (this.selectedBand) count++;
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

  // Back button handler for shared component
  returnToDashboard(): void {
    window.history.back();
  }
}
