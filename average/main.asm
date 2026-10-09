; print-macro.asm
%macro print 2
    mov rax, 1                              ; sys_write
    mov rdi, 1                              ; stdout выводим в терминал
    mov rsi, %2                             ; адрес строки (откуда из памяти брать буквы)
    mov rdx, %1                             ; сколько байт напечатать
    syscall
%endmacro

section .data
    colon_space db ": "                    
    cs_len      equ $ - colon_space        ; длина разделителя

    err_msg     db "файл испорчен", 0xA    ; текст ошибки
    err_len     equ $ - err_msg             

    minus_ch    db "-"                     ; символ минуса, если среднее выйдет отрицательным
    newline     db 0xA                      

section .bss
    buffer      resb 256                    ; буфер для прочитки файла
    count       resb 1                      ; память на 1 байт под ноль
    out_buf     resb 16                     ; массив на 16 ячеек, куда задом наперед запишем цифры числа
    fn_ptr      resq 1                      ; адрес имени файла из терминала
    fn_len      resq 1                      ; длина имени файла в символах

section .text
    global _start

_start:
    ; [rsp] = argc (количество аргументов в терминале)
    mov rax, [rsp]                          ; смотрим, сколько слов ввели при запуске в консоли
    cmp rax, 2                              ; должно быть имя программы и имя_файла.txt
    jl  exit_prog                           ; забыли указать — закрываем программу

    ; [rsp + 16] = argv[1] (адрес первого аргумента — текста "имя_файла.txt")
    mov rsi, [rsp + 16]                     ; адрес, где в оперативной памяти лежит имя файла
    mov [fn_ptr], rsi                       ; передаем адрес в fn_ptr

    ; Считаем длину имени файла, до нулевого байта
    xor rcx, rcx                            ; rcx = 0

find_fn_len:
    mov al, [rsi + rcx]                     ; берем очередную букву имени файла
    cmp al, 0                               ; дошли до 0 байта?
    je  found_fn_len                        ; да, переходим в found_fn_len
    inc rcx                                 ; нет, счетчик + 1
    jmp find_fn_len                         ; повтор

found_fn_len:
    mov [fn_len], rcx                       ; сохраняем полученную длину имени файла в память

    mov rax, 2                              ; sys_open
    mov rdi, [fn_ptr]                       ; отдаем системе адрес имени файла
    xor rsi, rsi                            ; O_RDONLY: берем файл только для чтения
    xor rdx, rdx                            ; mode (не используется для чтения)
    syscall

    cmp rax, 0                              ; проверяем полученный номер-дескриптор файла
    jl  corrupted_error                     ; < 0 => файл испорчен

    ; read(fd, buffer, 256)
    mov rdi, rax                            ; передаем этот номерок файла в rdi для следующей команды
    mov rax, 0                              ; sys_read
    mov rsi, buffer                         ; адрес нашего буфера
    mov rdx, 256                            ; ограничение 256 байт
    syscall

    cmp rax, 0                              ; в rax количество прочитанных байт
    jle corrupted_error                     ; <= 0 => файл испорчен

    mov rsi, buffer                         ; rsi = фдаг, указывающий на первый символ в буфере
    xor r8, r8                              ; r8 = 0 кол-во чисел в 1 строке
    xor r12, r12                            ; r12 = 0 сумма чисел 1 строки
    xor rbx, rbx                            ; rbx = 0 переменная для сборки подсчета числа
    xor r15, r15                            ; r15 = 0 (флаг: встретили ли хоть одну цифру в текущем числе)

parse_line1:
    mov al, [rsi]                           ; один текущий символ из памяти в регистр al

    cmp al, 0xA                             ; al = ('\n')?
    je  end_line1                           ; да, первая строка прочитана
    cmp al, 0                               ; внезапный обрыв файла?
    je  end_line1                           ; да, конец первой строки

    cmp al, ' '                             ; al = " "?
    je  next_char_1
    cmp al, 0xD                             ; символ возврата '\r' (из Windows)?
    je  next_char_1

    cmp al, ','                             ; al = ","
    je  save_number_1                       ; число закончилось => cохранение

    ; Проверка на буквы и мусор: цифра строго от '0' (код 48) до '9' (код 57)
    cmp al, '0'                             ; символ меньше чем '0'?
    jb  corrupted_error                     ; да => файл испорчен
    cmp al, '9'                             ; символ больше чем '9'?
    ja  corrupted_error                     ; да => файл испорчен

    ; Склейка цифр в единое число
    mov r15, 1                              ; цифра есть
    imul rbx, 10                            ; предыдущую часть в десятки
    sub  al, '0'                            ; символ превращаем в цифру
    movzx rax, al                           ; расщирение al на весь 64-битный регистр rax
    add  rbx, rax                           ; прибавляем цифру
    jmp  next_char_1                        

save_number_1:
    cmp r15, 0                              ; была ли цифра перед запятой?
    je  corrupted_error                     ; запятая в начале или (",,") => файл испорчен
    add r12, rbx                            ; прибавляем число во всю сумму 1 строки
    inc r8                                  ; увеличиваем счетчик найденных чисел
    xor r15, r15                            ; сбрасываем флаг
    xor rbx, rbx                            ; сбрасываем накопитель в 0
    jmp next_char_1

next_char_1:
    inc rsi                                 ; сдвигаем rsi на следующий байт памяти (двигаем указатель)
    jmp parse_line1                         

end_line1:
    add r12, rbx                            ; сумма 1 строки
    inc r8                                  ; прибавляем к количеству чисел в 1 строке
    xor rbx, rbx                            ; очищаем накопитель
    cmp r15, 0                              ; была ли цифра в конце строки перед переносом?
    je  corrupted_error                     ; если строка кончилась запятой ("7, \n") => файл испорчен
    inc rsi                                 ; перешагиваем через ('\n') к началу 2-й строки

    ; 2 строка
    xor r9, r9                              ; r9 = 0 кол-во чисел во 2 строке
    xor r13, r13                            ; r13 = 0 сумма чисел 2 строки
                                            
parse_line2:
    mov al, [rsi]   

    cmp al, 0xA
    je  end_line2
    cmp al, 0
    je  end_line2

    cmp al, ' '
    je  next_char_2
    cmp al, 0xD
    je  next_char_2

    cmp al, ',' 
    je  save_number_2

    cmp al, '0'
    jb  corrupted_error                     ; файл испорчен
    cmp al, '9'
    ja  corrupted_error                     ; файл испорчен

    mov r15, 1
    imul rbx, 10        
    sub  al, '0'
    movzx rax, al
    add  rbx, rax
    jmp  next_char_2

save_number_2:
    cmp r15, 0
    je  corrupted_error
    add r13, rbx
    inc r9                                  ; счетчик чисел второй строки + 1
    xor r15, r15
    xor rbx, rbx
    jmp next_char_2

next_char_2:
    inc rsi                                 ; двигаем указатель
    jmp parse_line2

end_line2:
    add r13, rbx    
    inc r9
    xor rbx, rbx
    cmp r15, 0
    je  corrupted_error

    cmp r8, r9                              ; сравнение r8 и r9
    jne corrupted_error                     ; r8 != r9 => файл испорчен

    cmp r8, 0                               ; есть ли числа в файле
    je  corrupted_error                     ; /0 => файл испорчен

    ; Среднее арифметическое
    ; Сумма разностей = сумма 1 строки - сумма 2 строки
    mov rax, r12                            ; сумма первой строки в rax
    sub rax, r13                            ; сумма 1 строки - сумма 2 строки

    cqo                                     ; растягиваем знак числа из rax в rdx:rax для знакового деления
    idiv r8                                 ; деление суммы разностей на количество чисел в строке

    ; Вывод
    push rax                                ; временно прячем ответ в стек, чтобы системный вызов его не затер

    ; Печатаем имя файла и двоеточие с пробелом
    print [fn_len], [fn_ptr]                ; выводим имя ("имя_файла.txt")
    print cs_len, colon_space               ; выводим разделитель (": ")

    pop rax                                 ; достаем ответ обратно из стека в rax

    ; Проверяем знак ответа
    cmp rax, 0                              ; ответ >= 0?
    jge print_positive                      ; да, выводим
    push rax                                ; < 0 => прячем число
    print 1, minus_ch                       ; выводим символ минуса в терминал
    pop rax                                 ; забираем число
    neg rax                                 ; делаем его положительным, чтобы правильно разобрать на цифры

print_positive:
    ; Отдельный случай для нуля
    cmp rax, 0                              ; ответ = 0?
    jne convert_to_digits                   ; нет, переходим в convert_to_digits
    mov byte [count], '0'                   ; кладем символ '0' в ячейку count
    print 1, count                          ; выводим 0
    jmp print_finish                        ; завершение программы

convert_to_digits:
    ; Раскладываем число на цифры делением на 10 и пишем их в буфер с конца к началу
    lea rdi, [out_buf + 15]                 ; rdi смотрит в самый конец буфера (заполняет задом наперед)
    mov rcx, 10                             ; / 10

digit_loop:
    xor rdx, rdx                            ; rdx = 0
    div rcx                                 ; rax / 10: последняя цифра падает в остаток rdx
    add dl, '0'                             ; из цифры ASCII символ
    dec rdi                                 ; шаг влево в буфере памяти
    mov [rdi], dl                           ; кладем символ цифры в эту ячейку
    test rax, rax                           ; осталось ли еще что-то от числа?
    jnz digit_loop                          ; если не ноль — продолжаем доставать цифры

    ; Выводим собранное число в терминал
    lea rdx, [out_buf + 15]                 ; берем конец буфера
    sub rdx, rdi                            ; вычитаем начало: получаем сколько точно цифр вышло в строке
    mov rsi, rdi                            ; адрес первой цифры
    mov rax, 1                              ; sys_write
    mov rdi, 1                              ; в терминал
    syscall

print_finish:
    print 1, newline                        
    jmp exit_prog

; Вывод ошибки
corrupted_error:
    print [fn_len], [fn_ptr]                ; выводим имя файла
    print cs_len, colon_space               ; выводим ": "
    print err_len, err_msg                  ; "файл испорчен\n"

exit_prog:
    mov rax, 60                             ; sys_exit
    xor rdi, rdi                            ; код выхода 0
    syscall