import { NextRequest, NextResponse } from "next/server";

const ACCESS_COOKIE = "onx_access_token";
const REFRESH_COOKIE = "onx_refresh_token";

const ACCESS_MAX_AGE = 60 * 30;
const REFRESH_MAX_AGE = 60 * 60 * 24 * 7;

function cookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge,
  };
}

export async function POST(request: NextRequest) {
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  if (!refreshToken) {
    return NextResponse.json({ detail: "Refresh token missing" }, { status: 401 });
  }

  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  const response = await fetch(`${apiUrl}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  const data = await response.json();
  const nextResponse = NextResponse.json(data, { status: response.status });

  if (!response.ok) {
    nextResponse.cookies.delete(ACCESS_COOKIE);
    nextResponse.cookies.delete(REFRESH_COOKIE);
    return nextResponse;
  }

  nextResponse.cookies.set(ACCESS_COOKIE, data.access_token, cookieOptions(ACCESS_MAX_AGE));
  nextResponse.cookies.set(REFRESH_COOKIE, data.refresh_token, cookieOptions(REFRESH_MAX_AGE));
  return nextResponse;
}
