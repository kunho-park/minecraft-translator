"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useSession } from "next-auth/react";
import { Star, Check, X, AlertCircle, Loader2, User } from "lucide-react";
import Button from "@/components/ui/Button";
import Image from "next/image";

interface Review {
  id: string;
  works: boolean;
  rating: number;
  comment: string | null;
  isAnonymous: boolean;
  createdAt: string;
  user: {
    name: string;
    avatar: string | null;
  } | null;
}

export default function ReviewPage() {
  const t = useTranslations();
  const router = useRouter();
  const params = useParams();
  const { data: session, status } = useSession();

  const packId = params.packId as string;

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [reviews, setReviews] = useState<Review[]>([]);

  // Form state
  const [works, setWorks] = useState<boolean | null>(null);
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comment, setComment] = useState("");

  useEffect(() => {
    fetchReviews();
  }, [packId]);

  const fetchReviews = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/reviews?packId=${packId}`);
      if (response.ok) {
        const data = await response.json();
        setReviews(data);
      }
    } catch (err) {
      console.error("Failed to fetch reviews:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (works === null || rating === 0) {
      setError(t("review.errors.required"));
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(false);

    try {
      const response = await fetch("/api/reviews", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          packId,
          works,
          rating,
          comment: comment || null,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error(t("review.errors.rateLimit"));
        }
        throw new Error(data.error || t("review.errors.failed"));
      }

      // Success
      setSuccess(true);
      
      // Refresh reviews
      fetchReviews();

      // Reset form
      setWorks(null);
      setRating(0);
      setComment("");

      // Redirect after short delay
      setTimeout(() => {
        router.back();
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("review.errors.failed"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 animate-fade-in">
      <h1 className="text-2xl font-bold text-[var(--text-primary)] mb-4">
        {t("review.writeReview")}
      </h1>

      {/* Anonymous notice */}
      {!session && status !== "loading" && (
        <div className="mb-6 p-4 rounded-lg bg-[var(--status-info)]/20 text-[var(--status-info)] flex items-start gap-3">
          <User className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">{t("review.anonymousNotice.title")}</p>
            <p className="text-sm opacity-80 mt-1">{t("review.anonymousNotice.description")}</p>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 rounded-lg bg-[var(--status-error)]/20 text-[var(--status-error)] flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          {error}
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 rounded-lg bg-[var(--status-success)]/20 text-[var(--status-success)] flex items-center gap-3">
          <Check className="w-5 h-5 flex-shrink-0" />
          {t("review.success")}
        </div>
      )}

      {/* Review Form */}
      <div className="glass rounded-xl p-6 mb-8">
        {/* Works or not */}
        <div className="mb-6">
          <label className="block text-sm text-[var(--text-secondary)] mb-3">
            {t("review.works.label")} *
          </label>
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => setWorks(true)}
              className={`flex-1 flex items-center justify-center gap-2 p-4 rounded-lg border-2 transition-all ${
                works === true
                  ? "border-[var(--status-success)] bg-[var(--status-success)]/20 text-[var(--status-success)]"
                  : "border-[var(--border-primary)] text-[var(--text-secondary)] hover:border-[var(--status-success)]"
              }`}
            >
              <Check className="w-5 h-5" />
              {t("review.works.yes")}
            </button>
            <button
              type="button"
              onClick={() => setWorks(false)}
              className={`flex-1 flex items-center justify-center gap-2 p-4 rounded-lg border-2 transition-all ${
                works === false
                  ? "border-[var(--status-error)] bg-[var(--status-error)]/20 text-[var(--status-error)]"
                  : "border-[var(--border-primary)] text-[var(--text-secondary)] hover:border-[var(--status-error)]"
              }`}
            >
              <X className="w-5 h-5" />
              {t("review.works.no")}
            </button>
          </div>
        </div>

        {/* Rating */}
        <div className="mb-6">
          <label className="block text-sm text-[var(--text-secondary)] mb-3">
            {t("review.rating")} *
          </label>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                onClick={() => setRating(star)}
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(0)}
                className="p-1 transition-transform hover:scale-110"
              >
                <Star
                  className={`w-8 h-8 transition-colors ${
                    star <= (hoverRating || rating)
                      ? "fill-yellow-400 text-yellow-400"
                      : "text-[var(--text-muted)]"
                  }`}
                />
              </button>
            ))}
          </div>
        </div>

        {/* Comment */}
        <div className="mb-6">
          <label className="block text-sm text-[var(--text-secondary)] mb-3">
            {t("review.comment")}
          </label>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder={t("review.commentPlaceholder")}
            rows={4}
            className="w-full resize-none"
          />
        </div>

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={() => router.back()}>
            {t("common.cancel")}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={submitting || works === null || rating === 0 || success}
            loading={submitting}
          >
            {t("review.submit")}
          </Button>
        </div>
      </div>

      {/* Existing Reviews */}
      <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">
        {t("review.title")} ({reviews.length})
      </h2>

      {loading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-[var(--accent-primary)]" />
        </div>
      ) : reviews.length > 0 ? (
        <div className="space-y-4">
          {reviews.map((review) => (
            <div key={review.id} className="card p-4">
              <div className="flex items-start gap-3">
                {review.user?.avatar ? (
                  <Image
                    src={review.user.avatar}
                    alt={review.user.name}
                    width={40}
                    height={40}
                    className="w-10 h-10 rounded-full"
                  />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center">
                    <User className="w-5 h-5 text-[var(--text-muted)]" />
                  </div>
                )}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-medium text-[var(--text-primary)]">
                      {review.user?.name || t("review.anonymous")}
                    </span>
                    {review.isAnonymous && (
                      <span className="text-xs text-[var(--text-muted)]">
                        ({t("review.anonymousLabel")})
                      </span>
                    )}
                    <span
                      className={`flex items-center gap-1 text-sm ${
                        review.works
                          ? "text-[var(--status-success)]"
                          : "text-[var(--status-error)]"
                      }`}
                    >
                      {review.works ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <X className="w-4 h-4" />
                      )}
                      {review.works ? t("review.works.yes") : t("review.works.no")}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 mb-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        className={`w-4 h-4 ${
                          star <= review.rating
                            ? "fill-yellow-400 text-yellow-400"
                            : "text-[var(--text-muted)]"
                        }`}
                      />
                    ))}
                  </div>
                  {review.comment && (
                    <p className="text-sm text-[var(--text-secondary)]">
                      {review.comment}
                    </p>
                  )}
                  <p className="text-xs text-[var(--text-muted)] mt-2">
                    {new Date(review.createdAt).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-center text-[var(--text-muted)] py-8">
          {t("review.noReviews")}
        </p>
      )}
    </div>
  );
}
