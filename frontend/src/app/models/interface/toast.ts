export interface Toast {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
  dismissible?: boolean;
  timestamp: Date;
}

export enum ToastType {
  SUCCESS = 'success',
  ERROR = 'error',
  INFO = 'info',
  WARNING = 'warning'
}

export interface ToastConfig {
  duration?: number;
  dismissible?: boolean;
  position?: ToastPosition;
}

export enum ToastPosition {
  TOP_RIGHT = 'top-right',
  TOP_LEFT = 'top-left',
  BOTTOM_RIGHT = 'bottom-right',
  BOTTOM_LEFT = 'bottom-left'
}

export interface ToastIcon {
  [ToastType.SUCCESS]: string;
  [ToastType.ERROR]: string;
  [ToastType.INFO]: string;
  [ToastType.WARNING]: string;
}