#include "pdf/mupdf_c_api.h"

#include <mupdf/fitz.h>

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PARIN_MAX_RENDER_EDGE 12000
#define PARIN_MAX_RENDER_PIXELS 16000000

struct parin_mupdf_document {
    fz_context *context;
    fz_document *document;
    int page_count;
};

static void set_error(char *buffer, size_t size, const char *message)
{
    if (buffer == NULL || size == 0)
        return;
    if (message == NULL || message[0] == '\0')
        message = "Unknown MuPDF error";
    snprintf(buffer, size, "%s", message);
}

static int valid_document(const parin_mupdf_document *document)
{
    return document != NULL && document->context != NULL && document->document != NULL;
}

parin_mupdf_document *parin_mupdf_open(
    const char *utf8_path,
    const char *password,
    char *error_buffer,
    size_t error_buffer_size)
{
    parin_mupdf_document *handle = NULL;
    fz_document *opened = NULL;

    if (utf8_path == NULL || utf8_path[0] == '\0') {
        set_error(error_buffer, error_buffer_size, "A PDF file path is required.");
        return NULL;
    }

    handle = (parin_mupdf_document *)calloc(1, sizeof(*handle));
    if (handle == NULL) {
        set_error(error_buffer, error_buffer_size, "Not enough memory to create a PDF session.");
        return NULL;
    }

    handle->context = fz_new_context(NULL, NULL, 64u * 1024u * 1024u);
    if (handle->context == NULL) {
        free(handle);
        set_error(error_buffer, error_buffer_size, "MuPDF could not create its rendering context.");
        return NULL;
    }

    fz_var(handle);
    fz_var(opened);
    fz_try(handle->context) {
        fz_register_document_handlers(handle->context);
        opened = fz_open_document(handle->context, utf8_path);
        if (fz_needs_password(handle->context, opened)) {
            const char *candidate_password = password != NULL ? password : "";
            if (!fz_authenticate_password(handle->context, opened, candidate_password))
                fz_throw(handle->context, FZ_ERROR_GENERIC, "This PDF requires a valid password.");
        }
        handle->page_count = fz_count_pages(handle->context, opened);
        if (handle->page_count < 1)
            fz_throw(handle->context, FZ_ERROR_GENERIC, "The PDF does not contain any pages.");
    }
    fz_catch(handle->context) {
        set_error(error_buffer, error_buffer_size, fz_caught_message(handle->context));
        if (opened != NULL)
            fz_drop_document(handle->context, opened);
        fz_drop_context(handle->context);
        free(handle);
        return NULL;
    }

    handle->document = opened;
    return handle;
}

void parin_mupdf_close(parin_mupdf_document *document)
{
    if (document == NULL)
        return;
    if (document->context != NULL) {
        if (document->document != NULL)
            fz_drop_document(document->context, document->document);
        fz_drop_context(document->context);
    }
    free(document);
}

int parin_mupdf_page_count(const parin_mupdf_document *document)
{
    return valid_document(document) ? document->page_count : 0;
}

int parin_mupdf_page_size(
    parin_mupdf_document *document,
    int page_index,
    float *width_points,
    float *height_points,
    char *error_buffer,
    size_t error_buffer_size)
{
    fz_page *page = NULL;
    fz_rect bounds;

    if (!valid_document(document) || page_index < 0 || page_index >= document->page_count ||
        width_points == NULL || height_points == NULL) {
        set_error(error_buffer, error_buffer_size, "Invalid PDF page size request.");
        return 0;
    }

    fz_var(page);
    fz_try(document->context) {
        page = fz_load_page(document->context, document->document, page_index);
        bounds = fz_bound_page(document->context, page);
        *width_points = bounds.x1 - bounds.x0;
        *height_points = bounds.y1 - bounds.y0;
        if (*width_points <= 0.0f || *height_points <= 0.0f)
            fz_throw(document->context, FZ_ERROR_GENERIC, "The PDF page has invalid dimensions.");
    }
    fz_catch(document->context) {
        set_error(error_buffer, error_buffer_size, fz_caught_message(document->context));
        if (page != NULL)
            fz_drop_page(document->context, page);
        return 0;
    }

    fz_drop_page(document->context, page);
    return 1;
}

int parin_mupdf_render_page(
    parin_mupdf_document *document,
    int page_index,
    float scale,
    uint8_t **pixels,
    int *width,
    int *height,
    int *stride,
    char *error_buffer,
    size_t error_buffer_size)
{
    fz_page *page = NULL;
    fz_pixmap *pixmap = NULL;
    fz_rect bounds;
    float estimated_width;
    float estimated_height;
    size_t byte_count;
    uint8_t *copy = NULL;

    if (pixels != NULL)
        *pixels = NULL;
    if (!valid_document(document) || page_index < 0 || page_index >= document->page_count ||
        pixels == NULL || width == NULL || height == NULL || stride == NULL ||
        !isfinite(scale) || scale <= 0.0f || scale > 16.0f) {
        set_error(error_buffer, error_buffer_size, "Invalid PDF render request.");
        return 0;
    }

    fz_var(page);
    fz_var(pixmap);
    fz_try(document->context) {
        page = fz_load_page(document->context, document->document, page_index);
        bounds = fz_bound_page(document->context, page);
        estimated_width = ceilf((bounds.x1 - bounds.x0) * scale);
        estimated_height = ceilf((bounds.y1 - bounds.y0) * scale);
        if (!isfinite(estimated_width) || !isfinite(estimated_height) ||
            estimated_width < 1.0f || estimated_height < 1.0f ||
            estimated_width > PARIN_MAX_RENDER_EDGE ||
            estimated_height > PARIN_MAX_RENDER_EDGE ||
            estimated_width * estimated_height > PARIN_MAX_RENDER_PIXELS) {
            fz_throw(document->context, FZ_ERROR_GENERIC, "The requested page render exceeds the safe pixel budget.");
        }
        pixmap = fz_new_pixmap_from_page(document->context, page,
            fz_scale(scale, scale), fz_device_rgb(document->context), 0);
    }
    fz_catch(document->context) {
        set_error(error_buffer, error_buffer_size, fz_caught_message(document->context));
        if (pixmap != NULL)
            fz_drop_pixmap(document->context, pixmap);
        if (page != NULL)
            fz_drop_page(document->context, page);
        return 0;
    }

    *width = pixmap->w;
    *height = pixmap->h;
    *stride = pixmap->stride;
    if (*width < 1 || *height < 1 || *width > PARIN_MAX_RENDER_EDGE ||
        *height > PARIN_MAX_RENDER_EDGE || *width > PARIN_MAX_RENDER_PIXELS / *height ||
        pixmap->n != 3 || pixmap->stride < *width * 3) {
        set_error(error_buffer, error_buffer_size, "MuPDF returned an unsafe or unsupported pixel buffer.");
        fz_drop_pixmap(document->context, pixmap);
        fz_drop_page(document->context, page);
        return 0;
    }

    byte_count = (size_t)(*stride) * (size_t)(*height);
    copy = (uint8_t *)malloc(byte_count);
    if (copy == NULL) {
        set_error(error_buffer, error_buffer_size, "Not enough memory for the rendered page.");
        fz_drop_pixmap(document->context, pixmap);
        fz_drop_page(document->context, page);
        return 0;
    }
    memcpy(copy, pixmap->samples, byte_count);
    fz_drop_pixmap(document->context, pixmap);
    fz_drop_page(document->context, page);
    *pixels = copy;
    return 1;
}

int parin_mupdf_search_page(
    parin_mupdf_document *document,
    int page_index,
    const char *utf8_query,
    char *error_buffer,
    size_t error_buffer_size)
{
    fz_quad boxes[128];
    int marks[128];
    int hits = 0;

    if (!valid_document(document) || page_index < 0 || page_index >= document->page_count ||
        utf8_query == NULL || utf8_query[0] == '\0') {
        set_error(error_buffer, error_buffer_size, "Invalid PDF search request.");
        return -1;
    }

    fz_var(hits);
    fz_try(document->context) {
        hits = fz_search_page_number(document->context, document->document, page_index,
            utf8_query, marks, boxes, 128);
    }
    fz_catch(document->context) {
        set_error(error_buffer, error_buffer_size, fz_caught_message(document->context));
        return -1;
    }
    return hits;
}

void parin_mupdf_free_buffer(void *buffer)
{
    free(buffer);
}
