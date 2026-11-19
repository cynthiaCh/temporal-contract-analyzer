export const columns = [
  { title: 'Order code', key: 'orderCode' },
  { title: 'Order name', key: 'orderName' },
];

export function publish(response: Response, selectedColumns: unknown[]) {
  console.log(response.status, selectedColumns);
}
