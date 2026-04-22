import { NextRequest, NextResponse } from "next/server";

const ACCESS_COOKIE = "onx_access_token";
const REFRESH_COOKIE = "onx_refresh_token";

export async function POST(request: NextRequest) {
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  if (refreshToken) {
    await fetch(`${apiUrl}/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  const response = NextResponse.json({ detail: "Logged out" });
  response.cookies.delete(ACCESS_COOKIE);
  response.cookies.delete(REFRESH_COOKIE);
  return response;
}
