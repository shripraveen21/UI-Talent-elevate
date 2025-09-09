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

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent implements OnInit {
  constructor(
    private fb: FormBuilder,
    private loginService: LoginService,
    private router: Router
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
        alert("loggin succ")
        this.router.navigate(['/mcq-quiz']);
      },
      error: () => {
        alert("failed login")
        
        this.error.set('Login failed (dummy).');
        this.loading.set(false);
      },
      complete: () => this.loading.set(false),
    });
  }
}
