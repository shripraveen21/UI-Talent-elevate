import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router, NavigationEnd } from '@angular/router';
import { LoginService } from '../../../services/login/login.service';
import { EmployeeService } from '../../../services/employee/employee.service';
import { Subscription } from 'rxjs';
import { filter } from 'rxjs/operators';

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

  constructor(
    private loginService: LoginService,
    private employeeService: EmployeeService
  ) { }

  ngOnInit(): void {
    this.loadUserInfo();
    this.checkNavbarVisibility();

    this.routerSubscription = this.router.events
      .pipe(filter(event => event instanceof NavigationEnd))
      .subscribe(() => {
        this.loadUserInfo();
        this.checkNavbarVisibility();
        this.showCollabMenu = false; // Hide menu on navigation
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
      default:
        return 'User';
    }
  }

    getRoleColor(): string {
    if (!this.userRole) return 'gray';
    switch (this.userRole) {
      case 'employee':
        return 'green';
      case 'capability_leader':
        return 'blue';
      case 'delivery_manager':
        return 'blue';
      case 'Employee':
        return 'green';
      case 'CapabilityLeader':
        return 'blue';
      case 'DeliveryManager':
        return 'blue';
      case 'ProductManager':
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
    this.router.navigate(['/add-techstack']);
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
