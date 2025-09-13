import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NavbarComponent } from './components/shared/navbar/navbar.component';
import { ToastContainerComponent } from './components/shared/toast/toast-container.component';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, NavbarComponent, ToastContainerComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'frontend';
}