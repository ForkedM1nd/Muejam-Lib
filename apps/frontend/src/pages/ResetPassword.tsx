import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, XCircle, Loader2, Eye, EyeOff } from "lucide-react";
import { api } from "@/lib/api";
import { validatePasswordStrength, type PasswordValidation } from "@/lib/passwordValidation";

export default function ResetPassword() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const token = searchParams.get("token");

    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [validation, setValidation] = useState<PasswordValidation | null>(null);

    const handlePasswordChange = (value: string) => {
        setPassword(value);
        setValidation(validatePasswordStrength(value));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!token) {
            setError("Invalid or missing reset token");
            return;
        }

        if (!validation?.isValid) {
            setError("Please meet all password requirements");
            return;
        }

        if (password !== confirmPassword) {
            setError("Passwords do not match");
            return;
        }

        setIsSubmitting(true);

        try {
            await api.resetPassword({ token, new_password: password });
            // Success - redirect to sign in
            navigate("/sign-in?reset=success");
        } catch (err: any) {
            setError(err?.error?.message || "Failed to reset password. The link may have expired.");
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!token) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
                <Card className="w-full max-w-md">
                    <CardHeader className="text-center">
                        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
                            <XCircle className="h-6 w-6 text-red-600" />
                        </div>
                        <CardTitle>Invalid reset link</CardTitle>
                        <CardDescription>
                            This password reset link is invalid or has expired.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Button asChild className="w-full">
                            <Link to="/forgot-password">Request a new reset link</Link>
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12">
            <Card className="w-full max-w-md">
                <CardHeader>
                    <CardTitle>Set new password</CardTitle>
                    <CardDescription>
                        Choose a strong password for your account.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {error && (
                            <Alert variant="destructive">
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}

                        <div className="space-y-2">
                            <Label htmlFor="password">New password</Label>
                            <div className="relative">
                                <Input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    placeholder="Enter new password"
                                    value={password}
                                    onChange={(e) => handlePasswordChange(e.target.value)}
                                    required
                                    disabled={isSubmitting}
                                    autoFocus
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                                >
                                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                            </div>

                            {password && validation && (
                                <div className="space-y-2 mt-3">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-gray-600">Password strength</span>
                                        <span className={`font-medium ${validation.strength === "strong" ? "text-green-600" :
                                                validation.strength === "medium" ? "text-yellow-600" :
                                                    "text-red-600"
                                            }`}>
                                            {validation.strength.charAt(0).toUpperCase() + validation.strength.slice(1)}
                                        </span>
                                    </div>
                                    <Progress value={validation.score * 25} className="h-2" />

                                    <ul className="space-y-1 text-sm">
                                        {validation.requirements.map((req) => (
                                            <li key={req.label} className="flex items-center gap-2">
                                                {req.met ? (
                                                    <CheckCircle2 className="h-4 w-4 text-green-600 flex-shrink-0" />
                                                ) : (
                                                    <XCircle className="h-4 w-4 text-gray-300 flex-shrink-0" />
                                                )}
                                                <span className={req.met ? "text-gray-700" : "text-gray-500"}>
                                                    {req.label}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="confirmPassword">Confirm new password</Label>
                            <div className="relative">
                                <Input
                                    id="confirmPassword"
                                    type={showConfirmPassword ? "text" : "password"}
                                    placeholder="Confirm new password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    required
                                    disabled={isSubmitting}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                                >
                                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                </button>
                            </div>
                            {confirmPassword && password !== confirmPassword && (
                                <p className="text-sm text-red-600">Passwords do not match</p>
                            )}
                        </div>

                        <Button
                            type="submit"
                            className="w-full"
                            disabled={isSubmitting || !validation?.isValid || password !== confirmPassword}
                        >
                            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Reset password
                        </Button>

                        <div className="text-center text-sm">
                            <Link to="/sign-in" className="text-primary hover:underline">
                                Back to sign in
                            </Link>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
