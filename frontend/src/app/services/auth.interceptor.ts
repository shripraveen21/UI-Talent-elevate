import { HttpInterceptorFn, HttpRequest, HttpHandlerFn, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';

export const authInterceptor: HttpInterceptorFn = (
  req: HttpRequest<any>,
  next: HttpHandlerFn
): Observable<HttpEvent<any>> => {
  // Do not add token for login endpoint
  if (req.url.endsWith('/login')) {
    // Add ngrok-skip-browser-warning header even for login requests
    const loginReq = req.clone({
      setHeaders: {
        'ngrok-skip-browser-warning': 'true' 
      }
    });
    return next(loginReq);
  }

  const token = localStorage.getItem('token');
  if (token) {
    const authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
        'ngrok-skip-browser-warning': 'true' 
      }
    });
    return next(authReq);
  }
  // Add ngrok-skip-browser-warning header even when no token is present
  const modifiedReq = req.clone({
    setHeaders: {
      'ngrok-skip-browser-warning': 'true' 
    }
  });
  return next(modifiedReq);
};