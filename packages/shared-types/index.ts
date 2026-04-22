export type UUID = string;

export type TenantContext = {
  tenant_id: UUID;
  branch_id: UUID;
};

export type Money = {
  currency: "VES" | "USD";
  amount: string;
};

export type ApiResponse<T> = {
  data: T;
  message?: string;
};
