import { CanActivateFn, Router } from '@angular/router';
import { LoginService } from '../services/login/login.service';
import { inject } from '@angular/core';

export const employeeGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);
  const auth = inject(LoginService);

  if (!auth.isAuthenticated()) {
    router.navigate(['/login']);
    return false;
  }
  if (auth.getUserRole() !== 'Employee') {
    router.navigate(['/unauthorized']);
    return false;
  }
  return true;
};
