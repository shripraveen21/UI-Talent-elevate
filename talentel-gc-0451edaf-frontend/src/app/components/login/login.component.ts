import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';
import { LoginService } from '../../services/login/login.service';
import { ToastService } from '../../services/toast/toast.service';
import { NgClass } from '@angular/common';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, NgClass],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent implements OnInit {
  constructor(
    private fb: FormBuilder,
    private loginService: LoginService,
    private router: Router,
    private toastService: ToastService
  ) {}

  form!: FormGroup;
  ngOnInit(): void {
    this.form = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(2)]],
    });
  }

  loading = signal(false);
  error = signal<string | null>(null);

  submit(): void {
    if (this.form.invalid || this.loading()) return;
    this.error.set(null);
    this.loading.set(true);
    const { email, password } = this.form.value;
    this.loginService.login(email, password).subscribe({
      next: (res) => {
        // store token (future: use a proper storage / state management)
        sessionStorage.setItem('auth_token', res.token);
        sessionStorage.setItem('user', JSON.stringify(res.user));
        
        // Show success toast
        this.toastService.showLoginSuccess();
        
        // Redirect based on user role
        const userRole = res.roles && res.roles.length > 0 ? res.roles[0] : null;
        this.redirectBasedOnRole(userRole);
      },
      error: (error) => {
        const errorMessage = error?.error?.message || 'Login failed. Please check your credentials and try again.';
        this.error.set(errorMessage);
        this.toastService.showLoginError(errorMessage);
        this.loading.set(false);
      },
      complete: () => this.loading.set(false),
    });
  }

  quickLogin(email: string): void {
    this.form.patchValue({
      email: email,
      password: '123456'
    });
    this.submit();
  }

  private redirectBasedOnRole(userRole: string | null): void {
    switch (userRole) {
      case 'Employee':
      case 'employee':
        this.router.navigate(['/employee-dashboard']);
        break;
      case 'CapabilityLeader':
      case 'capability_leader':
        this.router.navigate(['/capability-leader-dashboard']);
        break;
      case 'DeliveryManager':
      case 'delivery_manager':
        this.router.navigate(['/delivery-manager-dashboard']);
        break;
      case 'ProductManager':
      case 'product_manager':
        this.router.navigate(['/directory']);
        break;
      default:
        this.router.navigate(['/home']);
        break;
    }
  }
}