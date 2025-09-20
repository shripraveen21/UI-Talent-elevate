import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router, NavigationEnd } from '@angular/router';
import { LoginService } from '../../../services/login/login.service';
import { EmployeeService } from '../../../services/employee/employee.service';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';
import { PermissionsService } from '../../../services/auth/permissions.service';
import { TechStackAgentService } from '../../../services/techstack-agent/techstack-agent.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.css']
})
export class NavbarComponent implements OnInit, OnDestroy {
  isAuthenticated = false;
  user: any = null;
  userInfo: any = null;
  userRole: string | null = null;
  shouldShowNavbar = false;
  showCollabMenu = false;
  private routerSubscription?: Subscription;
  profile: any = null;
  showProfileModal: boolean = false;
  router = inject(Router);
  isUserCollaborator: boolean = false;
  canAssignTest: boolean = false;
  canCreateTest: boolean = false;
  canAccessTopics: boolean = false;

  constructor(
    private loginService: LoginService,
    private employeeService: EmployeeService,
    private permissionsService: PermissionsService,
    private techStackAgent: TechStackAgentService
  ) { }

ngOnInit(): void {
  this.loadUserInfo();
  this.checkNavbarVisibility();

  if (this.isAuthenticated && !['/', '/home', '/login'].includes(this.router.url)) {
    this.fetchPermissions();
  }

  this.routerSubscription = this.router.events
    .pipe(filter(event => event instanceof NavigationEnd))
    .subscribe(() => {
      this.loadUserInfo();
      this.checkNavbarVisibility();
      this.showCollabMenu = false;

      if (this.isAuthenticated && !['/', '/home', '/login'].includes(this.router.url)) {
        this.fetchPermissions();
      }
    });
}

fetchPermissions(): void {
  this.permissionsService.getUserPermissions().subscribe({
    next: (perms: any) => {
      this.isUserCollaborator = perms.isCollaborator === true;
      this.canAssignTest = perms.test_assign || false;
      this.canCreateTest = perms.test_create || false;
      this.canAccessTopics = perms.topics || false;
      this.userRole = perms.role || null;
    },
    error: (err) => {
      console.error('Error fetching permissions:', err);
      // Fallback: no permissions
      this.isUserCollaborator = false;
      this.canAssignTest = false;
      this.canCreateTest = false;
      this.canAccessTopics = false;
      this.userRole = null;
    }
  });
}

  ngOnDestroy(): void {
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }

  loadUserInfo(): void {
    this.isAuthenticated = this.loginService.isAuthenticated();
    if (this.isAuthenticated) {
      this.user = this.loginService.getCurrentUser();
      this.userInfo = this.loginService.getCurrentUser();
      this.userRole = this.loginService.getUserRole();
    } else {
      this.user = null;
      this.userInfo = null;
      this.userRole = null;
    }
  }

  checkNavbarVisibility(): void {
    const currentUrl = this.router.url;
    const hiddenRoutes = ['/', '/home', '/login'];
    this.shouldShowNavbar = this.isAuthenticated && !hiddenRoutes.includes(currentUrl);
  }

  getRoleDisplayName(): string {
    if (!this.userRole) return 'User';
    switch (this.userRole) {
      case 'employee':
      case 'Employee':
        return 'Employee';
      case 'capability_leader':
      case 'CapabilityLeader':
        return 'Capability Leader';
      case 'delivery_manager':
      case 'DeliveryManager':
        return 'Delivery Manager';
      case 'ProductManager':
        return 'Product Manager';
      case 'DeliveryLeader':
        return 'Deliver Leader';
      default:
        return 'User';
    }
  }

    getRoleColor(): string {
    if (!this.userRole) return 'gray';
    switch (this.userRole) {
      case 'Employee':
        return 'green';
      case 'CapabilityLeader':
        return 'blue';
      case 'DeliveryManager':
        return 'blue';
      case 'ProductManager':
        return 'orange';
      case 'DeliveryLeader':
        return 'orange';
      default:
        return 'gray';
    }
  }
 

  navigateToProfile(): void {
    this.employeeService.getProfile().subscribe({
      next: (data: any) => {
        this.profile = data;
        this.showProfileModal = true;
      },
      error: (error) => {
        console.error('Error fetching profile:', error);
        this.showProfileModal = true; // Show modal even if error, with fallback
      }
    });
  }

  closeProfileModal(): void {
    this.showProfileModal = false;
  }

  signOut(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('user');
    this.isAuthenticated = false;
    this.user = null;
    this.userInfo = null;
    this.userRole = null;
    this.shouldShowNavbar = false;
    this.router.navigate(['/home']);
  }

  navigateToHome(): void {
    this.router.navigate(['/home']);
  }

  navigateToDashboard(): void {
    switch (this.userRole) {
      case 'CapabilityLeader':
        this.router.navigate(['/capability-leader-dashboard']);
        break;
      case 'DeliveryManager':
        this.router.navigate(['/delivery-manager-dashboard']);
        break;
      case 'Employee':
        this.router.navigate(['/employee-dashboard']);
        break;
      default:
        this.router.navigate(['/dashboard']);
        break;
    }
  }

  // Collab menu navigation methods
  navigateToTopics(): void {
    this.showCollabMenu = false;
    this.techStackAgent.getCapabilityLeaderId().subscribe({
      next: (clId: number | null) => {
        if (!clId) {
          this.router.navigate(['/add-techstack']);
          return;
        }
        this.techStackAgent.getTopicsByLeader(clId).subscribe({
          next: (topics: any[]) => {
            if (topics && topics.length > 0) {
              this.router.navigate(['/collab-topics']);
            } else {
              this.router.navigate(['/add-techstack']);
            }
          },
          error: () => {
            this.router.navigate(['/add-techstack']);
          }
        });
      },
      error: () => {
        this.router.navigate(['/add-techstack']);
      }
    });
  }
  navigateToTests(): void {
    this.showCollabMenu = false;
    this.router.navigate(['/create-assessment']);
  }
  navigateToAssignTest(): void {
    this.showCollabMenu = false;
    this.router.navigate(['/directory']);
  }
  

  toggleCollabMenu(): void {
    this.showCollabMenu = !this.showCollabMenu;
  }
}
