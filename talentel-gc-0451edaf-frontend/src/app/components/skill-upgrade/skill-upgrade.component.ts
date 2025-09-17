import { Component, OnInit } from '@angular/core';
import { TechStackAgentService } from '../../services/techstack-agent/techstack-agent.service';
import { SkillUpgradeService } from '../../services/skill-upgrade.service';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SharedDropdownComponent } from '../shared/shared-dropdown/shared-dropdown.component';
import { BackButtonComponent } from '../shared/backbutton/backbutton.component';
import type { DropdownOption } from '../shared/shared-dropdown/shared-dropdown.component';

@Component({
  selector: 'app-skill-upgrade',
  templateUrl: './skill-upgrade.component.html',
  imports: [CommonModule, FormsModule, SharedDropdownComponent, BackButtonComponent]
})
export class SkillUpgradeComponent implements OnInit {
  techStacks: any[] = [];
  // Use DropdownOption type for strict compatibility with shared dropdown
  techStackDropdownOptions: DropdownOption[] = [];
  selectedTechStackDropdown: DropdownOption | null = null;

  levelOptions: DropdownOption[] = [
    { id: 'Beginner', name: 'Beginner' },
    { id: 'Intermediate', name: 'Intermediate' },
    { id: 'Advanced', name: 'Advanced' }
  ];
  selectedLevelDropdown: DropdownOption | null = null;

  testResult: any = null;
  error: string = '';
  token: string | null = "";
  loading: boolean = false;

  constructor(
    private techStackAgentService: TechStackAgentService,
    private skillUpgradeService: SkillUpgradeService,
    private router: Router
  ) { }

  ngOnInit() {
    this.token = localStorage.getItem('token');
    if (!this.token) {
      this.router.navigate(['/login']);
      return;
    }
    this.loadTechStacks();
  }

  loadTechStacks() {
    this.techStackAgentService.getTechStacks().subscribe({
      next: (stacks: any[]) => {
        this.techStacks = stacks;
        this.techStackDropdownOptions = stacks.map(stack => ({
          id: String(
            stack.id !== undefined
              ? stack.id
              : stack.tech_stack_id !== undefined
                ? stack.tech_stack_id
                : stack.name !== undefined
                  ? stack.name
                  : ''
          ),
          name: String(stack.name)
        }));
        console.log('Tech stacks loaded:', stacks);
      },
      error: (err) => {
        console.error('Error loading tech stacks:', err);
        this.techStacks = [];
        this.techStackDropdownOptions = [];
        this.error = 'Failed to load tech stacks from database';
      }
    });
  }

  returnToDashboard(): void {
    this.router.navigate(['/employee-dashboard']);
  }

  onTechStackSelection(option: DropdownOption) {
    this.selectedTechStackDropdown = option;
    this.error = '';
  }

  clearTechStack() {
    this.selectedTechStackDropdown = null;
  }

  onLevelSelection(option: DropdownOption) {
    this.selectedLevelDropdown = option;
    this.error = '';
  }

  clearLevel() {
    this.selectedLevelDropdown = null;
  }

  createTest() {
    if (!this.selectedTechStackDropdown) {
      this.error = 'Please select a tech stack';
      return;
    }
    if (!this.selectedLevelDropdown) {
      this.error = 'Please select a level';
      return;
    }

    this.token = localStorage.getItem('token');
    if (!this.token) {
      this.router.navigate(['/login']);
      return;
    }

    this.loading = true;
    this.error = '';

    // Use the tech stack name and level for the skill upgrade test
    const techStackName = this.selectedTechStackDropdown.name;

    // Map user-facing level to backend key
    const levelMap: { [key: string]: string } = {
      'Beginner': 'beginner',
      'Intermediate': 'intermediate',
      'Advanced': 'advanced'
    };
    const level = levelMap[String(this.selectedLevelDropdown.id)] || String(this.selectedLevelDropdown.id);

    // Pass both techStackName and mapped level to the service
    this.skillUpgradeService.createSkillUpgradeTest(this.token, techStackName, level).subscribe({
      next: (result) => {
        this.testResult = result;
        this.error = '';
        this.loading = false;
      },
      error: (err) => {
        console.error('Error creating test:', err);
        let errorMessage = 'Failed to create test';

        if (err.error) {
          if (typeof err.error === 'string') {
            errorMessage = err.error;
          } else if (err.error.detail) {
            errorMessage = err.error.detail;
          } else if (err.error.message) {
            errorMessage = err.error.message;
          }
        } else if (err.message) {
          errorMessage = err.message;
        }

        this.error = errorMessage;
        this.loading = false;
      }
    });
  }
}
