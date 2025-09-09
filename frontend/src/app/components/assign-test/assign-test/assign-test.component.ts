import { Component, OnInit } from '@angular/core';
import { EmployeeService } from '../../../services/employee/employee.service';
import { Employee } from '../../../models/interface/employee';
import { Test } from '../../../models/interface/test';
import { HttpClient } from '@angular/common/http';
import { TestListingService } from '../../../services/test-listing/test-listing.service';
import { environment } from '../../../../environments/environment';
import { FormsModule } from '@angular/forms';
import { JsonPipe, NgFor, NgIf } from '@angular/common';

@Component({
  selector: 'app-assign-test',
  templateUrl: './assign-test.component.html',
  styleUrls: ['./assign-test.component.css'],
  imports:[FormsModule,NgIf,NgFor,JsonPipe]
})
export class AssignTestComponent implements OnInit {
  employees: Employee[] = [];
  tests: Test[] = [];
  totalEmployees: number = 0;
  totalTests: number = 0;

  // For filtering
  bands: string[] = [];
  roles: string[] = [];
  skillLevels: string[] = [];
  selectedBand: string = '';
  selectedRole: string = '';
  selectedSkillLevel: string = '';
  search: string = '';
  testSearch: string = '';

  // Selection
  selectedEmployeeIds: number[] = [];
  selectedTestId: number | null = null;
  dueDate: string = '';

  // Assignment result
  assignmentResult: any = null;
  error: string = '';

  constructor(
    private employeeService: EmployeeService,
    private testListingService: TestListingService,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    this.getFilterOptions();
    this.getEmployees();
    this.getTests();
  }

  getFilterOptions(): void {
    this.employeeService.getEmployeeFilterOptions().subscribe(options => {
      this.bands = options.bands;
      this.roles = options.roles;
      this.skillLevels = options.skill_levels;
    });
  }

  getEmployees(): void {
    const params: any = {};
    if (this.selectedBand) params.band = this.selectedBand;
    if (this.selectedRole) params.designation = this.selectedRole;
    if (this.selectedSkillLevel) params.skill_level = this.selectedSkillLevel;
    if (this.search) params.search = this.search;
    this.employeeService.getEmployees(params).subscribe(res => {
      this.employees = res.employees;
      this.totalEmployees = res.total;
      // Reset selection if employees change
      this.selectedEmployeeIds = [];
    });
  }

  getTests(): void {
    const params: any = {};
    if (this.testSearch) params.search = this.testSearch;
    this.testListingService.getTests(params).subscribe(res => {
      this.tests = res.tests;
      this.totalTests = res.total;
    });
  }

  onEmployeeFilterChange(): void {
    this.getEmployees();
  }

  onTestSearchChange(): void {
    this.getTests();
  }

  onEmployeeCheckboxChange(empId: number, event: Event): void {
    const checked = (event.target as HTMLInputElement)?.checked ?? false;
    if (checked) {
      if (!this.selectedEmployeeIds.includes(empId)) {
        this.selectedEmployeeIds.push(empId);
      }
    } else {
      this.selectedEmployeeIds = this.selectedEmployeeIds.filter(id => id !== empId);
    }
  }

  assignTest(): void {
    if (!this.selectedTestId || this.selectedEmployeeIds.length === 0) {
      this.error = 'Please select a test and at least one employee.';
      return;
    }
    const payload = {
      user_ids: this.selectedEmployeeIds,
      test_id: this.selectedTestId,
      due_date: this.dueDate
    };
    this.http.post(environment.apiUrl + '/assign-test', payload).subscribe({
      next: (res) => {
        this.assignmentResult = res;
        this.error = '';
      },
      error: (err) => {
        this.assignmentResult = null;
        this.error = err.error?.detail || 'Assignment failed';
      }
    });
  }
}
