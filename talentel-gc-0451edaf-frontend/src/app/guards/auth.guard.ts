import { CanActivateFn, Router } from '@angular/router';
import { LoginService } from '../services/login/login.service';
import { inject } from '@angular/core';

export const authGuard: CanActivateFn = (route, state) => {
  const router = inject(Router);
  const auth = inject(LoginService);

  if (!auth.isAuthenticated()) {
    router.navigate(['/login']);
    return false;
  }

  // Role-based access control
  const allowedRoles: string[] = route.data?.['roles'];
  if (allowedRoles && allowedRoles.length > 0) {
    const userRole = auth.getUserRole?.();
    if (!userRole || !allowedRoles.includes(userRole)) {
      router.navigate(['/unauthorized']);
      return false;
    }
  }

  return true;
};
