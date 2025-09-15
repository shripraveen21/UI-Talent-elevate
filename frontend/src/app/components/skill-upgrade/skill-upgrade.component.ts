import { Component, OnInit } from '@angular/core';
import { TechStackAgentService } from '../../services/techstack-agent/techstack-agent.service';
import { SkillUpgradeService } from '../../services/skill-upgrade.service';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-skill-upgrade',
  templateUrl: './skill-upgrade.component.html',
  imports: [CommonModule, FormsModule]
})
export class SkillUpgradeComponent implements OnInit {
  techStacks: any[] = [];
  selectedTechStack: any = null;
  selectedLevel: string | null = null;
  testResult: any = null;
  error: string = '';
  token: string | null = "";
  loading: boolean = false;
  showTechStackDropdown: boolean = false;

  constructor(
    private techStackAgentService: TechStackAgentService,
    private skillUpgradeService: SkillUpgradeService,
    private router: Router
  ) {}

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
        console.log('Tech stacks loaded:', stacks);
      },
      error: (err) => {
        console.error('Error loading tech stacks:', err);
        this.techStacks = [];
        this.error = 'Failed to load tech stacks from database';
      }
    });
  }

  returnToDashboard(): void {
    this.router.navigate(['/employee-dashboard']);
  }

  selectTechStack(stack: any) {
    this.selectedTechStack = stack;
    this.showTechStackDropdown = false;
    this.error = '';
  }

  clearTechStack() {
    this.selectedTechStack = null;
  }

  createTest() {
    if (!this.selectedTechStack) {
      this.error = 'Please select a tech stack';
      return;
    }
    if (!this.selectedLevel) {
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
    const techStackName = this.selectedTechStack.name;
    const level = this.selectedLevel;
    
    // Pass both techStackName and level to the service
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
