export const columns = [
  { title: '订单编号', key: 'orderCode' },
  { title: '订单名称', key: 'orderName' },
];

export function publish(response: Response, selectedColumns: unknown[]) {
  console.log(response.status, selectedColumns);
}
