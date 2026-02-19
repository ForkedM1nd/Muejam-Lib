// ── Example Validated Form Component ──
// Demonstrates inline validation errors, field highlighting, and correction suggestions
// This component serves as a reference implementation for form validation patterns

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import {
    Form,
    FormControl,
    FormDescription,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

// Example validation schema with detailed error messages
const formSchema = z.object({
    email: z
        .string()
        .min(1, "Email is required")
        .email("Please enter a valid email address (e.g., user@example.com)"),
    password: z
        .string()
        .min(8, "Password must be at least 8 characters. Use at least 8 characters for better security")
        .regex(
            /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
            "Password must include uppercase, lowercase, and numbers. Include uppercase, lowercase, numbers, and special characters"
        ),
    username: z
        .string()
        .min(3, "Username must be at least 3 characters. Use at least 3 characters")
        .max(20, "Username must be at most 20 characters")
        .regex(
            /^[a-zA-Z0-9_]+$/,
            "Username can only contain letters, numbers, and underscores. Use only letters, numbers, and underscores"
        ),
    bio: z
        .string()
        .max(500, "Bio must be at most 500 characters")
        .optional(),
});

type FormValues = z.infer<typeof formSchema>;

interface ExampleValidatedFormProps {
    onSubmit: (values: FormValues) => Promise<void>;
    defaultValues?: Partial<FormValues>;
}

export function ExampleValidatedForm({ onSubmit, defaultValues }: ExampleValidatedFormProps) {
    const form = useForm<FormValues>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            email: defaultValues?.email || "",
            password: defaultValues?.password || "",
            username: defaultValues?.username || "",
            bio: defaultValues?.bio || "",
        },
        mode: "onBlur", // Validate on blur for better UX
    });

    const handleSubmit = async (values: FormValues) => {
        try {
            await onSubmit(values);
        } catch (error) {
            // Handle API validation errors
            if (error && typeof error === 'object' && 'error' in error) {
                const apiError = error as { error?: { field_errors?: Record<string, string[]> } };
                if (apiError.error?.field_errors) {
                    // Set form errors from API response
                    Object.entries(apiError.error.field_errors).forEach(([field, messages]) => {
                        form.setError(field as keyof FormValues, {
                            message: messages[0],
                        });
                    });
                }
            }
        }
    };

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
                {/* Email Field */}
                <FormField
                    control={form.control}
                    name="email"
                    render={({ field, fieldState }) => (
                        <FormItem>
                            <FormLabel>Email</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    type="email"
                                    placeholder="user@example.com"
                                    error={!!fieldState.error}
                                />
                            </FormControl>
                            <FormDescription>
                                We'll never share your email with anyone else.
                            </FormDescription>
                            <FormMessage />
                        </FormItem>
                    )}
                />

                {/* Password Field */}
                <FormField
                    control={form.control}
                    name="password"
                    render={({ field, fieldState }) => (
                        <FormItem>
                            <FormLabel>Password</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    type="password"
                                    placeholder="Enter a strong password"
                                    error={!!fieldState.error}
                                />
                            </FormControl>
                            <FormDescription>
                                Must be at least 8 characters with uppercase, lowercase, and numbers.
                            </FormDescription>
                            <FormMessage />
                        </FormItem>
                    )}
                />

                {/* Username Field */}
                <FormField
                    control={form.control}
                    name="username"
                    render={({ field, fieldState }) => (
                        <FormItem>
                            <FormLabel>Username</FormLabel>
                            <FormControl>
                                <Input
                                    {...field}
                                    placeholder="johndoe"
                                    error={!!fieldState.error}
                                />
                            </FormControl>
                            <FormDescription>
                                Your unique username (3-20 characters, letters, numbers, and underscores only).
                            </FormDescription>
                            <FormMessage />
                        </FormItem>
                    )}
                />

                {/* Bio Field (Optional) */}
                <FormField
                    control={form.control}
                    name="bio"
                    render={({ field, fieldState }) => (
                        <FormItem>
                            <FormLabel>Bio (Optional)</FormLabel>
                            <FormControl>
                                <Textarea
                                    {...field}
                                    placeholder="Tell us about yourself..."
                                    error={!!fieldState.error}
                                />
                            </FormControl>
                            <FormDescription>
                                A brief description about yourself (max 500 characters).
                            </FormDescription>
                            <FormMessage />
                        </FormItem>
                    )}
                />

                <Button type="submit" disabled={form.formState.isSubmitting}>
                    {form.formState.isSubmitting ? "Submitting..." : "Submit"}
                </Button>
            </form>
        </Form>
    );
}
