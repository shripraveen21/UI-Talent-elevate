export interface Test {
  id: number;
  test_name: string;
  description?: string;
  [key: string]: any;
}
