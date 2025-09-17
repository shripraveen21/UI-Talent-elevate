import { BrowserModule } from '@angular/platform-browser';

import { NgModule } from '@angular/core';

import { AppRoutingModule } from './app-routing.module';

import { AppComponent } from './app.component';
import { SharedDropdownComponent } from './components/shared/shared-dropdown/shared-dropdown.component';

import { NavbarComponent } from './components/shared/navbar/navbar.component';
import { ToastContainerComponent } from './components/shared/toast/toast-container.component';

@NgModule({
  imports: [
    BrowserModule,
    AppRoutingModule,
    AppComponent,
    NavbarComponent,
    ToastContainerComponent,
    SharedDropdownComponent
  ],
  providers: []
})
export class AppModule { }
