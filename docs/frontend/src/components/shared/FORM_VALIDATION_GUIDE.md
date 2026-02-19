# Form Validation Guide

This guide explains how to implement form validation with inline errors, field highlighting, and correction suggestions in the MueJam Library frontend.

## Features

✅ **Inline validation errors** - Errors display directly below form fields  
✅ **Field highlighting** - Invalid fields are highlighted with red borders  
✅ **Correction suggestions** - Helpful hints guide users to fix errors  
✅ **Accessible** - Proper ARIA attributes for screen readers  
✅ **Type-safe** - Full TypeScript support with Zod schemas  

## Quick Start

### 1. Basic Form with Validation

```tsx
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

// Define validation schema
const formSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Please enter a valid email address (e.g., user@example.com)"),
});

function MyForm() {
  const form = useForm({
    resolver: zodResolver(formSchema),
    defaultValues: { email: "" },
    mode: "onBlur", // Validate on blur for better UX
  });

  const onSubmit = async (values) => {
    // Handle form submission
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
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
                  error={!!fieldState.error}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit">Submit</Button>
      </form>
    </Form>
  );
}
```

### 2. Handling API Validation Errors

```tsx
import { extractValidationErrors, toFormErrors } from "@/lib/formValidation";

const onSubmit = async (values) => {
  try {
    await api.submitForm(values);
  } catch (error) {
    // Extract validation errors from API response
    const validationErrors = extractValidationErrors(error);
    
    // Convert to react-hook-form format
    const formErrors = toFormErrors(validationErrors);
    
    // Set errors on form
    Object.entries(formErrors).forEach(([field, error]) => {
      form.setError(field, error);
    });
  }
};
```

### 3. Custom Error Messages with Suggestions

The validation utilities automatically provide helpful suggestions based on the field and error type:

```tsx
// Email errors
"Invalid email format" 
→ "Invalid email format. Please enter a valid email address (e.g., user@example.com)"

// Password errors
"Password too short"
→ "Password too short. Use at least 8 characters for better security"

"Password too weak"
→ "Password too weak. Include uppercase, lowercase, numbers, and special characters"

// Username errors
"Username already taken"
→ "Username already taken. Try adding numbers or underscores to make it unique"

"Invalid characters"
→ "Invalid characters. Use only letters, numbers, and underscores"
```

## Validation Schema Best Practices

### 1. Include Helpful Error Messages

```tsx
const schema = z.object({
  password: z
    .string()
    .min(8, "Password must be at least 8 characters. Use at least 8 characters for better security")
    .regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      "Password must include uppercase, lowercase, and numbers. Include uppercase, lowercase, numbers, and special characters"
    ),
});
```

### 2. Use Descriptive Field Names

```tsx
// Good - matches API field names
const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  handle: z.string().min(3),
});

// Avoid - generic names
const schema = z.object({
  field1: z.string(),
  field2: z.string(),
});
```

### 3. Validate on Blur for Better UX

```tsx
const form = useForm({
  resolver: zodResolver(schema),
  mode: "onBlur", // Validate when user leaves field
  // mode: "onChange", // Too aggressive, validates on every keystroke
  // mode: "onSubmit", // Only validates on submit
});
```

## Component Props

### Input Component

```tsx
<Input
  error={boolean}  // Highlights field with red border
  {...field}       // Spread react-hook-form field props
/>
```

### Textarea Component

```tsx
<Textarea
  error={boolean}  // Highlights field with red border
  {...field}       // Spread react-hook-form field props
/>
```

### FormMessage Component

Automatically displays error messages from react-hook-form:

```tsx
<FormMessage />  // Shows error.message if present
```

## Accessibility

All form components include proper ARIA attributes:

- `aria-invalid` - Set to `true` when field has error
- `aria-describedby` - Links to error message and description
- `id` attributes - Properly linked labels and inputs

## Example: Complete Registration Form

See `ExampleValidatedForm.tsx` for a complete implementation demonstrating:
- Multiple field types (text, email, password, textarea)
- Client-side validation with Zod
- Server-side validation error handling
- Field highlighting
- Inline error messages
- Correction suggestions
- Accessible markup

## Testing

Test your form validation:

```tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

it('should display validation error', async () => {
  render(<MyForm />);
  
  const input = screen.getByLabelText('Email');
  await userEvent.type(input, 'invalid-email');
  await userEvent.tab(); // Trigger onBlur validation
  
  await waitFor(() => {
    expect(screen.getByText(/Please enter a valid email/)).toBeInTheDocument();
  });
  
  // Check field is highlighted
  expect(input).toHaveAttribute('aria-invalid', 'true');
});
```

## Common Patterns

### Password Confirmation

```tsx
const schema = z.object({
  password: z.string().min(8),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match. Make sure both password fields are identical",
  path: ["confirmPassword"],
});
```

### Conditional Validation

```tsx
const schema = z.object({
  hasWebsite: z.boolean(),
  website: z.string().optional(),
}).refine((data) => {
  if (data.hasWebsite) {
    return z.string().url().safeParse(data.website).success;
  }
  return true;
}, {
  message: "Please enter a valid URL. Enter a complete URL starting with http:// or https://",
  path: ["website"],
});
```

### Async Validation

```tsx
const checkUsernameAvailable = async (username: string) => {
  const response = await api.checkUsername(username);
  return response.available;
};

// In form
const onBlur = async (e) => {
  const username = e.target.value;
  const available = await checkUsernameAvailable(username);
  
  if (!available) {
    form.setError('username', {
      message: 'Username already taken. Try adding numbers or underscores to make it unique',
    });
  }
};
```

## Troubleshooting

### Error not displaying

- Check that `FormMessage` is included in `FormItem`
- Verify field name matches schema
- Ensure `error` prop is passed to Input/Textarea

### Field not highlighting

- Confirm `error={!!fieldState.error}` is set on Input/Textarea
- Check that fieldState is destructured from render prop

### Suggestions not showing

- Verify error message includes field name or error type keywords
- Check `formValidation.ts` for supported field types
- Add custom suggestions in `getFieldSuggestion` function

## Related Files

- `src/components/ui/form.tsx` - Form components
- `src/components/ui/input.tsx` - Input with error state
- `src/components/ui/textarea.tsx` - Textarea with error state
- `src/lib/formValidation.ts` - Validation utilities
- `src/components/shared/ExampleValidatedForm.tsx` - Complete example
