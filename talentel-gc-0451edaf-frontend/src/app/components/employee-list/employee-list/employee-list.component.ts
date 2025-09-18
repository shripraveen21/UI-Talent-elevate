import { Component, OnInit } from '@angular/core';
import { EmployeeService } from '../../../services/employee/employee.service';
import { Employee } from '../../../models/interface/employee';
import { FormsModule } from '@angular/forms';
import { NgFor } from '@angular/common';

@Component({
  selector: 'app-employee-list',
  templateUrl: './employee-list.component.html',
  styleUrls: ['./employee-list.component.css'],
  imports:[FormsModule,NgFor]
})
export class EmployeeListComponent implements OnInit {
  employees: Employee[] = [];
  total: number = 0;

  // Filter options
  bands: string[] = [];
  roles: string[] = [];
  skillLevels: string[] = [];

  // Selected filters
  selectedBand: string = '';
  selectedRole: string = '';
  selectedSkillLevel: string = '';
  search: string = '';

  constructor(private employeeService: EmployeeService) { }

  ngOnInit(): void {
    this.getFilterOptions();
    this.getEmployees();
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
      this.total = res.total;
    });
  }

  onFilterChange(): void {
    this.getEmployees();
  }

  onSearchChange(): void {
    this.getEmployees();
  }
}
