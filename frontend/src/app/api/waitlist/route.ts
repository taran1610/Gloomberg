import { NextRequest, NextResponse } from "next/server";
import { getSupabaseAdmin } from "@/lib/supabase-server";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const email = typeof body?.email === "string" ? body.email.trim().toLowerCase() : "";
    if (!email) {
      return NextResponse.json(
        { error: "Email is required" },
        { status: 400 }
      );
    }
    if (!EMAIL_REGEX.test(email)) {
      return NextResponse.json(
        { error: "Please enter a valid email address" },
        { status: 400 }
      );
    }

    const supabase = getSupabaseAdmin();
    if (!supabase) {
      const hint =
        process.env.NODE_ENV === "development"
          ? " Add NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY to frontend/.env.local (see frontend/.env.example)."
          : "";
      return NextResponse.json(
        { error: `Waitlist is not configured. Please try again later.${hint}` },
        { status: 503 }
      );
    }

    const { error } = await supabase
      .from("waitlist")
      .insert({ email });

    if (error) {
      if (error.code === "23505") {
        return NextResponse.json(
          { error: "This email is already on the waitlist." },
          { status: 409 }
        );
      }
      console.error("Waitlist insert error:", error);
      const msg =
        process.env.NODE_ENV === "development"
          ? error.message || "Could not join waitlist. Please try again."
          : "Could not join waitlist. Please try again.";
      return NextResponse.json({ error: msg }, { status: 500 });
    }

    return NextResponse.json({ success: true, message: "You're on the list!" });
  } catch (e) {
    console.error("Waitlist API error:", e);
    return NextResponse.json(
      { error: "Something went wrong. Please try again." },
      { status: 500 }
    );
  }
}
