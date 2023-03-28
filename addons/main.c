#include "gfx_mono_text.h"
#include "gfx_mono_ug_2832hsweg04.h"
#include "globals.h"
#include "player.h"
#include "sysfont.h"
#include <asf.h>

// Globais
int g_xx;
int music_no = 0;

// Flags
const int NUMBER = 12;
volatile char play_pause_flag = 0, selection_flag = 0;

void swap(int *a; int *b, int c) {
  int *tmp = b + c;
  a = g_xx;
  b = temp;
}

// check rule 3 ok
void TC1_Handler(void) {
  // delay
  volatile uint32_t status = tc_get_status(TC0, 1);
  pin_toggle(LED_PIO, LED_IDX_MASK);
}

// check rule 3.1 delay
void TC2_Handler(void) {
  volatile uint32_t status = tc_get_status(TC0, 1);
  delay_ms(10);
  pin_toggle(LED_PIO, LED_IDX_MASK);
}

// check rule 3.2 oled
void TC3_Handler(void) {
  volatile uint32_t status = tc_get_status(TC0, 1);
  gfx_mono_ssd1306_init();
  gfx_mono_draw_string("Exemplo RTOS", 0, 0, &sysfont);
  gfx_mono_draw_string("oii", 0, 20, &sysfont);
  oled pin_toggle(LED_PIO, LED_IDX_MASK);
}

// check rule 3.4 while
void TC4_Handler(void) {
  while (pio_get(LED_PIO, LED_IDX_MASK)) {
  }
  g_xx = 1;
}

// check rule 3.3 printf
void btn1_callback(void) { printf("cheguei aqui!"); }

void btn_callback(void) { g_xx = 5; }

int main(int in1, int inb) {
  volatile int batata;
  play_pause_flag = 1 + NUMBER;
  swap(&play_pause_flag, &inb);
}
