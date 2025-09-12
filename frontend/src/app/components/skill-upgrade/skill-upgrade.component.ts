import { Component, OnInit } from '@angular/core';
import { SkillUpgradeService, TechStack } from '../../services/skill-upgrade.service';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-skill-upgrade',
  templateUrl: './skill-upgrade.component.html',
  imports: [CommonModule, FormsModule]
})
export class SkillUpgradeComponent implements OnInit {
  techStacks: TechStack[] = [];
  selectedTechStackName: string = '';
  testResult: any = null;
  error: string = '';
  token: string | null = "";
  loading: boolean = false

  constructor(private skillUpgradeService: SkillUpgradeService, private router: Router) {}

  ngOnInit() {
    this.token = localStorage.getItem('token')
    if (!this.token) {
      this.router.navigate(['/login'])
      return
    }
    this.skillUpgradeService.getUserTechStacks(this.token).subscribe({
      next: (data) => this.techStacks = data,
      error: () => this.error = 'Failed to load tech stacks'
    });
  }

  createTest() {
    if (!this.selectedTechStackName) {
      this.error = 'Please select a tech stack';
      return;
    }
    this.token = localStorage.getItem('token')
    if (!this.token) {
      this.router.navigate(['/login'])
      return
    }

    this.loading = true;
    this.skillUpgradeService.createSkillUpgradeTest(this.token, this.selectedTechStackName).subscribe({
      next: (result) => {
        this.testResult = result;
        this.error = '';
        this.loading = false;
      },
      error: (err) => {
        this.error = err.error?.detail || 'Failed to create test';
        this.loading = false;
      }
    });
  }
}