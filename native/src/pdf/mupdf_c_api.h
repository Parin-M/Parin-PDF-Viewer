#ifndef PARIN_MUPDF_C_API_H
#define PARIN_MUPDF_C_API_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct parin_mupdf_document parin_mupdf_document;

parin_mupdf_document *parin_mupdf_open(
    const char *utf8_path,
    const char *password,
    char *error_buffer,
    size_t error_buffer_size
);

void parin_mupdf_close(parin_mupdf_document *document);
int parin_mupdf_page_count(const parin_mupdf_document *document);

int parin_mupdf_page_size(
    parin_mupdf_document *document,
    int page_index,
    float *width_points,
    float *height_points,
    char *error_buffer,
    size_t error_buffer_size
);

int parin_mupdf_render_page(
    parin_mupdf_document *document,
    int page_index,
    float scale,
    uint8_t **pixels,
    int *width,
    int *height,
    int *stride,
    char *error_buffer,
    size_t error_buffer_size
);

int parin_mupdf_search_page(
    parin_mupdf_document *document,
    int page_index,
    const char *utf8_query,
    char *error_buffer,
    size_t error_buffer_size
);

void parin_mupdf_free_buffer(void *buffer);

#ifdef __cplusplus
}
#endif

#endif
