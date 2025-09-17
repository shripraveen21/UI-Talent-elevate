import { Component, inject, OnInit } from '@angular/core';
import { EmployeeService } from '../../services/employee/employee.service';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

@Component({
  selector: 'app-profile-page',
  templateUrl: './profile-page.component.html',
  styleUrls: ['./profile-page.component.css'],
  standalone: true,
  imports: [CommonModule]
})
export class ProfilePageComponent implements OnInit {
  profile: any = null;
  loading = true;
  error = '';
  router = inject(Router);

  constructor(private employeeService: EmployeeService) {}

  ngOnInit(): void {
    this.employeeService.getProfile().subscribe({
      next: (data) => {
        this.profile = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error fetching profile';
        this.loading = false;
      }
    });
  }

  getProfileImage(): string {
    return 'https://ui-avatars.com/api/?name=' + 
           encodeURIComponent(this.profile?.name || 'User') + 
           '&background=3b82f6&color=ffffff&size=200&font-size=0.6';
  }

  getSkillLevelClass(level: string): string {
    const levelLower = level?.toLowerCase();
    switch (levelLower) {
      case 'expert':
      case 'advanced':
        return 'skill-expert';
      case 'intermediate':
      case 'medium':
        return 'skill-intermediate';
      case 'beginner':
      case 'basic':
        return 'skill-beginner';
      default:
        return 'skill-default';
    }
  }

  getSkillIcon(level: string): string {
    const levelLower = level?.toLowerCase();
    switch (levelLower) {
      case 'expert':
      case 'advanced':
        return '⭐';
      case 'intermediate':
      case 'medium':
        return '🔥';
      case 'beginner':
      case 'basic':
        return '🌱';
      default:
        return '📚';
    }
  }
}