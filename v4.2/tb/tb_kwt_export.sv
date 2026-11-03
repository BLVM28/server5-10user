`timescale 1ns/1ps
// Local bridge to the software consumer. Capture actual bus memory at the
// first successful response for each of the first twelve cold tasks.
module tb_kwt_export;
  tb_kwt_system #(.COMPACT(1)) checked();
  integer count=0,index,fd;
  reg held=0;
  always @(posedge checked.nice_clk)begin
    if(checked.nice_rst_n && checked.nice_rsp_valid && !held && !checked.nice_rsp_err && checked.check_mac && count<12)begin
      fd=$fopen($sformatf("physical_layer%02d.hex",count),"w");
      if(!fd)$fatal(1,"cannot open DUT capture");
      for(index=0;index<12896;index=index+1)$fwrite(fd,"%08x\n",checked.memory[checked.YI+index]);
      $fclose(fd);count=count+1;
    end
    held<=checked.nice_rst_n && checked.nice_rsp_valid;
  end
endmodule
