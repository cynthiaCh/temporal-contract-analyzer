import { publish, columns } from './shared';

// Demonstration input only. The analyzer and context generator never execute it.
export async function loadOrders() {
  const response = await fetch('/api/orders');
  publish(response, columns);
}
