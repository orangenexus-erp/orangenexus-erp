export type AuthTokens = {
  accessToken: string;
  refreshToken: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type UserJwtPayload = {
  sub: string;
  tenant_id: string;
  role: string;
  branch_id: string;
  exp: number;
  iat: number;
};
